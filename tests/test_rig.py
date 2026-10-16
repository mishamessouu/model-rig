import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from rig import ROOT, STATE, check, report, run
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

    def test_rescore_sees_a_changed_score(self):
        from rig.rescore import rescore
        out, _ = batch(["fake-s1"])
        path = out / "runs" / "fake-s1.open.r1" / "result.json"
        row = json.loads(path.read_text())
        row["fixed"] = []
        path.write_text(json.dumps(row))
        self.assertEqual(rescore(out, echo=lambda *_: None), 1)
        self.assertEqual(json.loads(path.read_text())["fixed"], ["s1-sql-injection"])


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
        from rig.harness import claude
        with tempfile.TemporaryDirectory() as folder:
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
