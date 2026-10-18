import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from rig import ROOT, STATE, check, prices, report, run
from rig.__main__ import main
from rig.harness import parse_claude, parse_codex

# tests/__init__.py points the state folder at a scratch folder.
assert "model-rig-state-" in str(STATE)

MATRIX = run.load_matrix(ROOT / "tests" / "matrix-fake.toml")


def batch(cells, prompts=("open",)):
    results = tempfile.mkdtemp(prefix="model-rig-results-")
    out, rows = run.run_batch("booking-ladder", MATRIX, list(cells), list(prompts),
                              1, results_root=results, echo=lambda *_: None)
    return out, {row["cell"]: row for row in rows}


class ScenarioTest(unittest.TestCase):
    def test_booking_ladder_is_sound(self):
        self.assertEqual(check.check("booking-ladder"), [])

    def test_check_flags_weak_tests_and_wrong_fixes_that_pass(self):
        import dataclasses
        import shutil
        import subprocess
        from unittest import mock

        from rig import scenario as scenarios
        real = scenarios.load("booking-ladder")
        with tempfile.TemporaryDirectory() as folder:
            copy = Path(folder) / "booking-ladder"
            shutil.copytree(real.folder, copy)
            # A "wrong" fix that is the real s1 fix scores as a success.
            repo = scenarios.copy_repo(real, Path(folder) / "repo")
            scenarios.overlay(real.solution("s1-sql-injection"), repo)
            patch = subprocess.run(["git", "-C", str(repo), "diff"],
                                   capture_output=True, text=True).stdout
            (copy / "wrong").mkdir()
            (copy / "wrong" / "real.patch").write_text(patch)
            # A defect test that passes on the unfixed code measures nothing.
            defects = [dict(d) for d in real.defects]
            defects[0]["tests"] = defects[0]["tests"] + ["hidden.test_regression"]
            fake = dataclasses.replace(real, folder=copy, defects=defects)
            with mock.patch("rig.check.scenarios.load", return_value=fake):
                problems = check.check("booking-ladder")
        self.assertIn("baseline already passes defect tests ['hidden.test_regression']",
                      problems)
        self.assertIn("wrong/real.patch scores as a success: ['s1-sql-injection']",
                      problems)

    def test_every_scenario_loads_with_its_files(self):
        # No prepare step: this checks the small files a pull request adds.
        from rig import scenario as scenarios
        names = sorted(p.parent.name for p in ROOT.glob("scenarios/*/scenario.toml"))
        self.assertIn("wger-log-idor", names)
        for name in names:
            with self.subTest(scenario=name):
                scenario = scenarios.load(name)
                self.assertEqual(scenario.name, name)
                self.assertTrue(scenario.prompts)
                self.assertTrue(any(scenario.hidden.iterdir()))
                for defect in scenario.defects:
                    self.assertTrue(defect["tests"], defect["id"])
                    solution = scenario.solution(defect.get("solution", defect["id"]))
                    self.assertTrue(solution.is_dir(), solution)


class PipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Sign-in folders exist, so the probe proves the sandbox hides them.
        for folder, name in (("claude-config", ".credentials.json"),
                             ("codex-home", "auth.json")):
            Path(STATE, folder).mkdir(exist_ok=True)
            Path(STATE, folder, name).write_text("{}")
        cls.out, cls.rows = batch(["fake-none", "fake-s1", "fake-probe"])

    def test_reference_fix_scores_as_its_defect(self):
        row = self.rows["fake-s1"]
        self.assertEqual(row["fixed"], ["s1-sql-injection"])
        self.assertTrue(row["regression_pass"])
        self.assertEqual(row["diff"]["files"], 1)
        self.assertEqual(row["choice"], "fake s1-sql-injection")

    def test_no_change_fixes_nothing(self):
        row = self.rows["fake-none"]
        self.assertEqual(row["fixed"], [])
        self.assertTrue(row["regression_pass"])
        self.assertEqual(row["diff"]["files"], 0)

    def test_tokens_and_credits(self):
        row = self.rows["fake-s1"]
        self.assertEqual(row["tokens"], {"input": 1000, "output": 2000,
                                         "cache_read": 100000, "cache_write": 10000})
        # 1k*400 + 2k*2000 + 100k*20 + 10k*500, per million tokens.
        self.assertEqual(row["costs"]["copilot"]["value"], 11.4)

    def test_sandbox_hides_rig_sign_in_and_sockets(self):
        self.assertEqual(self.rows["fake-probe"]["final"], "PROBE []")

    def test_work_folders_removed(self):
        self.assertEqual(list(Path(STATE, "work").rglob("*.json")), [])

    def test_files_written(self):
        for name in ("result.json", "diff.patch", "agent-log.jsonl.gz"):
            self.assertTrue((self.out / "runs" / "fake-s1.open.r1" / name).exists())
        self.assertIn("rig_commit", json.loads((self.out / "batch.json").read_text()))

    def test_report_rows(self):
        text = report.markdown(self.out)
        self.assertIn("| fake-s1 | open | 1 | s1-sql-injection x1 | 1/1 |", text)
        self.assertIn("| fake-none | open | 1 | no change x1 | 0/1 |", text)


class RescoreTest(unittest.TestCase):
    def test_rescore_keeps_score_and_history(self):
        from rig.rescore import rescore
        out, _ = batch(["fake-none", "fake-s1"])
        self.assertEqual(rescore(out, echo=lambda *_: None), 0)
        row = json.loads((out / "runs" / "fake-s1.open.r1" / "result.json").read_text())
        self.assertEqual(row["fixed"], ["s1-sql-injection"])
        self.assertEqual(row["previous_scores"][0]["fixed"], ["s1-sql-injection"])

    def test_committed_fix_keeps_its_diff_and_score(self):
        # An agent that commits its work must not leave an empty patch,
        # or a rescore would score the clean fixture as no fix.
        from rig.rescore import rescore
        out, rows = batch(["fake-s1-commit"])
        row = rows["fake-s1-commit"]
        self.assertEqual(row["fixed"], ["s1-sql-injection"])
        self.assertEqual(row["diff"]["files"], 1)
        self.assertTrue((out / "runs" / "fake-s1-commit.open.r1" / "diff.patch").read_text())
        self.assertEqual(rescore(out, echo=lambda *_: None), 0)

    def test_rescore_sees_a_changed_score(self):
        from rig.rescore import rescore
        out, _ = batch(["fake-s1"])
        path = out / "runs" / "fake-s1.open.r1" / "result.json"
        row = json.loads(path.read_text())
        row["fixed"] = []
        path.write_text(json.dumps(row))
        self.assertEqual(rescore(out, echo=lambda *_: None), 1)
        self.assertEqual(json.loads(path.read_text())["fixed"], ["s1-sql-injection"])


class ResumeTest(unittest.TestCase):
    def test_resume_runs_only_missing(self):
        out, _ = batch(["fake-none"])
        _, rows = run.run_batch("booking-ladder", MATRIX, ["fake-none", "fake-s1"],
                                ["open"], 1, echo=lambda *_: None, resume=out)
        self.assertEqual([row["cell"] for row in rows], ["fake-s1"])
        self.assertEqual(len(list(out.glob("runs/*/result.json"))), 2)
        self.assertEqual(json.loads((out / "batch.json").read_text())["resumed"][0]["runs"], 1)

    def test_resume_clears_a_stopped_run(self):
        out, _ = batch(["fake-none"])
        batch_name = json.loads((out / "batch.json").read_text())["batch"]
        # A stopped run leaves its work folder behind.
        (STATE / "work" / batch_name / "fake-s1.open.r1" / "home").mkdir(parents=True)
        _, rows = run.run_batch("booking-ladder", MATRIX, ["fake-s1"], ["open"], 1,
                                echo=lambda *_: None, resume=out)
        self.assertEqual(rows[0]["fixed"], ["s1-sql-injection"])


class ScorePatchTest(unittest.TestCase):
    def test_patch_that_does_not_apply_fixes_nothing(self):
        from rig import scenario as scenarios
        from rig.score import score_patch
        bad = "--- a/nope.py\n+++ b/nope.py\n@@ -1 +1 @@\n-old\n+new\n"
        with tempfile.TemporaryDirectory() as folder:
            scored, error = score_patch(scenarios.load("booking-ladder"), bad, folder)
        self.assertIsNone(scored)
        self.assertTrue(error)


class CostTest(unittest.TestCase):
    def test_no_usage_is_unknown_not_zero(self):
        sheet = prices.load()["copilot"]
        self.assertEqual(prices.cost(sheet, {}), (None, ["no usage recorded"]))


def result(cell="c", fixed=("s1",), error=None, timed_out=False, by_model=None):
    return {"cell": cell, "prompt": "open", "fixed": list(fixed), "regression_pass": True,
            "error": error, "timed_out": timed_out, "diff": {"files": 1, "added": 1,
            "removed": 0}, "by_model": by_model if by_model is not None else
            {"m": {"input": 1_000_000, "output": 0, "cache_read": 0, "cache_write": 0}},
            "tokens": {"input": 1, "output": 1, "cache_read": 1, "cache_write": 1},
            "usd_reported": None, "seconds": 1, "costs": {}}


class ReportTest(unittest.TestCase):
    SHEETS = {"s": {"unit": "credits", "models": {
        "m": {"input": 10, "output": 0, "cache_read": 0, "cache_write": 0}}}}

    def row(self, runs):
        return report.summarise(runs, sheet="s", sheets=self.SHEETS)[0]

    def test_timed_out_run_is_not_a_success(self):
        row = self.row([result(), result(timed_out=True)])
        self.assertEqual(row["success"], 1)
        self.assertEqual(row["errors"], 1)

    def test_cost_comes_from_stored_tokens_and_todays_sheet(self):
        # The run stored no cost; the sheet prices its tokens now.
        row = self.row([result(), result()])
        self.assertEqual(row["mean_cost"], 10.0)
        self.assertEqual(row["cost_per_success"], 10.0)

    def test_one_unpriced_run_makes_the_cell_cost_unknown(self):
        row = self.row([result(), result(by_model={})])
        self.assertIsNone(row["mean_cost"])
        self.assertIsNone(row["cost_per_success"])

    def test_three_of_three_has_a_wide_interval(self):
        low, high = report.wilson(3, 3)
        self.assertAlmostEqual(low, 0.438, places=3)
        self.assertEqual(high, 1.0)
        self.assertIsNone(report.wilson(0, 0))


class CodexParseTest(unittest.TestCase):
    def test_cached_tokens_move_out_of_input(self):
        log = "\n".join([
            json.dumps({"type": "thread.started"}),
            json.dumps({"type": "turn.completed", "usage": {
                "input_tokens": 5000, "cached_input_tokens": 4000, "output_tokens": 300}}),
            json.dumps({"type": "turn.completed", "usage": {
                "input_tokens": 7000, "cached_input_tokens": 6000, "output_tokens": 200}}),
        ])
        parsed = parse_codex(log, model="gpt-6-luna")
        self.assertEqual(parsed["by_model"]["gpt-6-luna"],
                         {"input": 2000, "output": 500, "cache_read": 10000, "cache_write": 0})
        self.assertIsNone(parsed["error"])

    def test_no_finished_turn_has_no_usage(self):
        # A Codex run cut off by the timeout writes no turn.completed event.
        log = json.dumps({"type": "thread.started"})
        parsed = parse_codex(log, model="gpt-6-luna")
        self.assertEqual(parsed["by_model"], {})
        self.assertEqual(parsed["error"], "no turn.completed event")


class ClaudeParseTest(unittest.TestCase):
    def test_failed_run_names_its_reason(self):
        log = "\n".join([
            json.dumps({"type": "system", "subtype": "init"}),
            json.dumps({"type": "result", "subtype": "success", "is_error": True,
                        "terminal_reason": "api_error", "modelUsage": {},
                        "result": "Not logged in"}),
        ])
        parsed = parse_claude(log)
        self.assertEqual(parsed["error"], "api_error: Not logged in")
        self.assertEqual(parsed["by_model"], {})


class ClaudeInvocationTest(unittest.TestCase):
    def test_one_agent_no_background_no_web(self):
        from unittest import mock

        from rig.harness import claude
        # CI has no Claude Code, and this test only reads the argv.
        with tempfile.TemporaryDirectory() as folder, \
                mock.patch("rig.harness._real", return_value=Path("/usr/bin/claude")):
            run_dir = Path(folder)
            invocation = claude({"model": "opus"}, "fix it", run_dir, 1.0)
        argv = [str(part) for part in invocation.argv]
        denied = argv[argv.index("--disallowedTools") + 1].split(",")
        for tool in ("Agent", "ScheduleWakeup", "Monitor", "WebSearch", "WebFetch",
                     "EnterWorktree"):
            self.assertIn(tool, denied)
        self.assertEqual(invocation.env["CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"], "1")


class GuardTest(unittest.TestCase):
    def test_real_runs_need_yes(self):
        with contextlib.redirect_stdout(io.StringIO()) as said:
            code = main(["run", "booking-ladder", "--cells", "claude-opus-medium",
                         "--prompts", "open", "--repeats", "1"])
        self.assertEqual(code, 2)
        self.assertIn("--yes", said.getvalue())


if __name__ == "__main__":
    unittest.main()
