import contextlib
import io
import json
import socket
import socketserver
import tempfile
import threading
import unittest
from pathlib import Path

from rig import ROOT, STATE, check, prices, proxy, report, run
from rig.__main__ import main
from rig.harness import parse_claude, parse_codex

# tests/__init__.py points the state folder at a scratch folder.
assert "model-rig-state-" in str(STATE)

MATRIX = run.load_matrix(ROOT / "tests" / "matrix-fake.toml")


def batch(cells, prompts=("open",), matrix=MATRIX):
    results = tempfile.mkdtemp(prefix="model-rig-results-")
    out, rows = run.run_batch("booking-ladder", matrix, list(cells), list(prompts),
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

    def test_check_holds_right_fixes_to_their_named_defects(self):
        import dataclasses
        import shutil
        import subprocess
        from unittest import mock

        from rig import scenario as scenarios
        real = scenarios.load("booking-ladder")
        with tempfile.TemporaryDirectory() as folder:
            copy = Path(folder) / "booking-ladder"
            shutil.copytree(real.folder, copy)
            repo = scenarios.copy_repo(real, Path(folder) / "repo")
            scenarios.overlay(real.solution("s1-sql-injection"), repo)
            patch = subprocess.run(["git", "-C", str(repo), "diff"],
                                   capture_output=True, text=True).stdout
            (copy / "right").mkdir()
            (copy / "right" / "named.patch").write_text(
                "The real s1 fix.\nFixes: s1-sql-injection\n\n" + patch)
            (copy / "right" / "too-much.patch").write_text(
                "Fixes: s1-sql-injection, s2-cancel-idor\n\n" + patch)
            (copy / "right" / "unnamed.patch").write_text(patch)
            fake = dataclasses.replace(real, folder=copy)
            with mock.patch("rig.check.scenarios.load", return_value=fake):
                problems = check.check("booking-ladder")
        self.assertEqual(sorted(p for p in problems if p.startswith("right/")), [
            "right/too-much.patch fixes ['s1-sql-injection'] with regression pass True, "
            "expected ['s1-sql-injection', 's2-cancel-idor']",
            "right/unnamed.patch has no 'Fixes:' line",
        ])

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


def control_scenario(folder, regression=("hidden.test_regression",), extra=""):
    """A control scenario in `folder`: booking-ladder's app and hidden
    regression tests, `control = true`, and no defects. Returns its path."""
    import shutil
    real = ROOT / "scenarios" / "booking-ladder"
    copy = Path(folder) / "control-ladder"
    shutil.copytree(real / "repo", copy / "repo")
    shutil.copytree(real / "hidden", copy / "hidden")
    tests = ", ".join(f'"{t}"' for t in regression)
    (copy / "scenario.toml").write_text(
        'name = "control-ladder"\ncontrol = true\n' + extra +
        '\n[prompts]\nopen = "Find the one improvement that matters most."\n'
        f'\n[regression]\ntests = [{tests}]\n')
    return copy


class ControlTest(unittest.TestCase):
    """A control has nothing to find (design decision 12)."""

    def test_control_loads_with_no_defects(self):
        from rig import scenario as scenarios
        with tempfile.TemporaryDirectory() as folder:
            scenario = scenarios.load(str(control_scenario(folder)))
        self.assertTrue(scenario.control)
        self.assertEqual(scenario.defects, [])

    def test_control_with_defects_or_plain_without_is_refused(self):
        from rig import scenario as scenarios
        defect = '\n[[defects]]\nid = "d1"\ntests = ["hidden.test_defects"]\n'
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(SystemExit):
                scenarios.load(str(control_scenario(folder, extra=defect)))
        with tempfile.TemporaryDirectory() as folder:
            path = control_scenario(folder)
            toml = path / "scenario.toml"
            toml.write_text(toml.read_text().replace("control = true\n", ""))
            with self.assertRaises(SystemExit):
                scenarios.load(str(path))

    def test_check_passes_a_sound_control(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(check.check(str(control_scenario(folder))), [])

    def test_check_refuses_fix_folders_and_a_failing_baseline(self):
        with tempfile.TemporaryDirectory() as folder:
            path = control_scenario(
                folder, regression=("hidden.test_regression", "hidden.test_defects"))
            for name in ("solutions", "wrong"):
                (path / name).mkdir()
            problems = check.check(str(path))
        self.assertEqual(problems, [
            "a control has no solutions/ folder",
            "a control has no wrong/ folder",
            "baseline fails regression tests ['hidden.test_defects']",
        ])

    def test_control_run_records_no_fix_and_its_report_counts_outcomes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = control_scenario(folder)
            out, rows = run.run_batch(str(path), MATRIX, ["fake-none"], ["open"], 1,
                                      results_root=Path(folder) / "results",
                                      echo=lambda *_: None)
            text = report.markdown(out)
        self.assertEqual(rows[0]["fixed"], [])
        self.assertTrue(rows[0]["regression_pass"])
        self.assertTrue(rows[0]["control"])
        self.assertIn("1 control runs.", text)
        self.assertIn("| fake-none | open | 1 | 0 | 1/1 (21% to 100%) | 0/1 (0% to 79%) | "
                      "0/1 (0% to 79%) | 0/1 (0% to 79%) |", text)
        self.assertNotIn("Success means", text)
        # No success column: a control run is never a success or a miss.
        self.assertNotIn("| Success |", text)


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
        self.assertEqual(row["diff"]["paths"], ["bookings/repository.py"])
        self.assertEqual(row["choice"], "fake s1-sql-injection")

    def test_no_change_fixes_nothing(self):
        row = self.rows["fake-none"]
        self.assertEqual(row["fixed"], [])
        self.assertTrue(row["regression_pass"])
        self.assertEqual(row["diff"]["files"], 0)
        self.assertEqual(row["diff"]["paths"], [])

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


class SandboxHideTest(unittest.TestCase):
    """The rig checkout, the state folder, and home stay hidden even when
    no emptied folder holds them, as for a rig run as root from /root."""

    def test_rig_state_and_home_are_emptied_before_any_bind(self):
        from unittest import mock

        from rig import sandbox
        with mock.patch.object(sandbox, "ROOT", Path("/opt/rig")), \
                mock.patch.object(sandbox, "STATE", Path("/opt/rig-state")), \
                mock.patch.object(Path, "exists", return_value=True), \
                mock.patch.object(Path, "home", return_value=Path("/root")):
            argv = sandbox.command(["true"], cwd="/opt/rig-state/work/r/repo",
                                   read=["/opt/rig-state/envs/x"],
                                   write=["/opt/rig-state/work/r"])
        pairs = list(zip(argv, argv[1:]))
        for path in ("/opt/rig", "/opt/rig-state", "/root"):
            self.assertIn(("--tmpfs", path), pairs)
        # The run's own folders come back after the hiding.
        self.assertLess(argv.index("/opt/rig-state"), argv.index("/opt/rig-state/envs/x"))
        self.assertLess(argv.index("/opt/rig-state"), argv.index("/opt/rig-state/work/r"))

    def test_a_path_under_an_emptied_folder_or_root_is_not_hidden_again(self):
        from unittest import mock

        from rig import sandbox
        with mock.patch.object(sandbox, "ROOT", Path("/home/u/rig")), \
                mock.patch.object(sandbox, "STATE", Path("/tmp/state")), \
                mock.patch.object(Path, "home", return_value=Path("/")):
            self.assertEqual(sandbox.hidden_paths(), [])

    @unittest.skipIf(any(Path.home().resolve().is_relative_to(p) for p in
                         ("/home", "/data", "/tmp", "/run", "/var", "/mnt", "/media",
                          "/srv", "/snap")) or Path.home() == Path("/"),
                     "home already sits in an emptied folder")
    def test_a_state_folder_outside_the_emptied_folders_is_unreadable(self):
        import subprocess
        from unittest import mock

        from rig import sandbox
        with tempfile.TemporaryDirectory(dir=Path.home()) as folder:
            state = Path(folder)
            (state / "claude-config").mkdir()
            secret = state / "claude-config" / ".credentials.json"
            secret.write_text("{}")
            (state / "envs").mkdir()
            (state / "envs" / "marker").write_text("env")
            with mock.patch.object(sandbox, "STATE", state, create=True):
                command = sandbox.command(
                    ["sh", "-c", 'cat "$1" 2>/dev/null; echo; cat "$2"', "-",
                     str(secret), str(state / "envs" / "marker")],
                    cwd="/", read=[state / "envs"])
            done = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(done.stdout.split(), ["env"])


class RuntimeRestoreTest(unittest.TestCase):
    """Restore runtime installs without restoring private parent folders."""

    @contextlib.contextmanager
    def layout(self, kind):
        from unittest import mock

        from rig import sandbox, scenario as scenarios
        with tempfile.TemporaryDirectory() as folder, contextlib.ExitStack() as stack:
            base = Path(folder)
            home, root, state = [base / name for name in ("home", "checkout", "state")]
            for path in (home, root, state):
                path.mkdir()
                (path / "private-marker").write_text("private")
            # Exercise dynamic masks without requiring a writable /opt or /root.
            stack.enter_context(mock.patch.object(sandbox, "EMPTIED", ()))
            stack.enter_context(mock.patch.object(sandbox, "ROOT", root))
            stack.enter_context(mock.patch.object(sandbox, "STATE", state))
            stack.enter_context(mock.patch.object(scenarios, "STATE", state))
            stack.enter_context(mock.patch.object(Path, "home", return_value=home))
            scenario = scenarios.Scenario("demo", root, {}, [], [], setup=[], kind=kind)
            (scenario.env / "bin").mkdir(parents=True)
            (scenario.env / "allowed-marker").write_text("allowed")
            yield scenario, (home, root, state)

    def point_runtime(self, scenario, install):
        if scenario.kind == "python":
            (scenario.env / "pyvenv.cfg").write_text(f"home = {install}/bin\n")
        binary = "python3" if scenario.kind == "python" else "node"
        link = scenario.env / "bin" / binary
        link.unlink(missing_ok=True)
        link.symlink_to(install / "bin" / binary)
        return link

    def assert_private(self, scenario, private):
        import subprocess

        from rig import sandbox
        argv = sandbox.command(
            ["/bin/sh", "-c", 'for p do test ! -e "$p" || exit 11; done; '
             'cat "$ALLOWED_MARKER"', "-", *[p / "private-marker" for p in private]],
            cwd="/", read=scenario.sandbox_read(),
            env={"ALLOWED_MARKER": scenario.env / "allowed-marker"})
        done = subprocess.run(argv, capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout, "allowed")

    def assert_runtime_restored(self, kind):
        import shutil
        import subprocess

        from rig import sandbox
        binary = "python3" if kind == "python" else "node"
        system = shutil.which(binary)
        self.assertIsNotNone(system, f"{binary} is required")
        with self.layout(kind) as (scenario, private):
            for parent in private:
                with self.subTest(parent=parent.name):
                    install = parent / "runtime"
                    (install / "bin").mkdir(parents=True)
                    (install / "bin" / binary).symlink_to(system)
                    named = parent / "runtime-link"
                    named.symlink_to(install, target_is_directory=True)
                    executable = self.point_runtime(scenario, named)
                    reads = scenario.sandbox_read()
                    done = subprocess.run(sandbox.command(
                        [executable, "--version"], cwd="/", read=reads),
                        capture_output=True, text=True)
                    self.assertEqual(done.returncode, 0, done.stderr)
                    self.assertTrue(done.stdout.strip())
                    self.assertEqual(reads, [scenario.env, named, install])
                    self.assert_private(scenario, private)

    def test_python_install_under_each_dynamic_mask_starts(self):
        self.assert_runtime_restored("python")

    def test_node_install_under_each_dynamic_mask_starts(self):
        self.assert_runtime_restored("node")

    def assert_private_parents_not_restored(self, kind):
        with self.layout(kind) as (scenario, private):
            home, root, state = private
            for install in (home, root, state, home.parent):
                alias = home / f"alias-{install.name}"
                alias.symlink_to(install, target_is_directory=True)
                for named in (install, alias):
                    with self.subTest(install=named):
                        self.point_runtime(scenario, named)
                        self.assertEqual(scenario.sandbox_read(), [scenario.env])
                        self.assert_private(scenario, private)

    def test_python_install_cannot_restore_checkout_or_state_parents(self):
        self.assert_private_parents_not_restored("python")

    def test_node_install_cannot_restore_checkout_or_state_parents(self):
        self.assert_private_parents_not_restored("node")


class NetworkTest(unittest.TestCase):
    """The sandbox has no network of its own. A cell with hosts reaches
    them through the proxy only, and the run records what it tried."""

    @classmethod
    def setUpClass(cls):
        cls.echo = cls.enterClassContext(echo_server())
        matrix = json.loads(json.dumps(MATRIX))
        for cell in matrix["cells"]:
            if cell["name"] == "fake-netprobe":
                cell["hosts"] = [cls.echo]
        cls.out, cls.rows = batch(["fake-netprobe", "fake-netprobe-offline", "fake-none"],
                                  matrix=matrix)

    def probe(self, cell):
        final = self.rows[cell]["final"]
        self.assertTrue(final.startswith("NETPROBE "), final)
        return json.loads(final[len("NETPROBE "):])

    def test_allowed_host_through_proxy_and_nothing_else(self):
        seen = self.probe("fake-netprobe")
        # A direct connect fails at once: the namespace has loopback only.
        self.assertNotEqual(seen["direct"], "open")
        self.assertLess(seen["direct_seconds"], 2)
        self.assertEqual(seen["dns"], "fails")
        self.assertEqual(seen["proxy"], "http://127.0.0.1:3128")
        self.assertEqual(seen["allowed"], {self.echo: "echo"})
        self.assertEqual(seen["denied"], 403)
        self.assertEqual(self.rows["fake-netprobe"]["network"],
                         {"allowed": ["127.0.0.1"], "denied": ["denied.example.invalid"]})
        log = self.out / "runs" / "fake-netprobe.open.r1" / "network.jsonl"
        self.assertEqual(len(log.read_text().splitlines()), 2)

    def test_cells_without_hosts_get_no_network(self):
        seen = self.probe("fake-netprobe-offline")
        self.assertNotEqual(seen["direct"], "open")
        self.assertEqual(seen["dns"], "fails")
        self.assertIsNone(seen["proxy"])
        self.assertEqual(seen["bridge"], "ECONNREFUSED")
        for cell in ("fake-netprobe-offline", "fake-none"):
            self.assertEqual(self.rows[cell]["network"], {"allowed": [], "denied": []})
            log = self.out / "runs" / f"{cell}.open.r1" / "network.jsonl"
            self.assertEqual(log.read_text(), "")

    def test_report_names_runs_with_a_denied_host(self):
        text = report.markdown(self.out)
        self.assertIn("fake-netprobe.open.r1 (denied.example.invalid)", text)
        self.assertNotIn("fake-none.open.r1 (", text)


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


class BatchDirTest(unittest.TestCase):
    def test_a_second_batch_in_the_same_second_takes_the_next_second(self):
        import datetime
        first = datetime.datetime(2026, 10, 23, 20, 25, 3, tzinfo=datetime.UTC)
        times = iter([first, first, first + datetime.timedelta(seconds=1)])
        waits = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = run.new_batch_dir(root, "s", now=lambda: first)
            b = run.new_batch_dir(root, "s", now=lambda: next(times), wait=waits.append)
            self.assertEqual(a.name, "20261023T202503Z-s")
            self.assertEqual(b.name, "20261023T202504Z-s")
            self.assertEqual(waits, [1, 1])


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

    def test_the_longest_matching_key_prices_a_model(self):
        # Sonnet 5 and Sonnet 5.5 differ in cache read price, and one id
        # starts with the other. The order of keys must not decide.
        sheet = {"models": {
            "claude-sonnet-5": {"input": 0, "output": 0, "cache_read": 20, "cache_write": 0},
            "claude-sonnet-5-5": {"input": 0, "output": 0, "cache_read": 10, "cache_write": 0},
        }}
        tokens = {"cache_read": 1_000_000}
        self.assertEqual(prices.cost(sheet, {"claude-sonnet-5-5": tokens}), (10.0, []))
        self.assertEqual(prices.cost(sheet, {"claude-sonnet-5": tokens}), (20.0, []))


def result(cell="c", fixed=("s1",), error=None, timed_out=False, by_model=None,
           fix_after_cutoff=None):
    return {"cell": cell, "prompt": "open", "fixed": list(fixed), "regression_pass": True,
            "fix_after_cutoff": fix_after_cutoff,
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

    def test_fix_after_cutoff_column(self):
        for value, shown in ((True, "yes"), (False, "no"), (None, "unknown")):
            with self.subTest(value=value):
                row = self.row([result(fix_after_cutoff=value)])
                self.assertEqual(row["fix_after_cutoff"], shown)

    def control(self, files=1, paths=("app/views.py",), **changes):
        """A clean control run: scored, regression set passing."""
        run = {**result(fixed=()), "control": True, "tests": {"t": {"passed": True}},
               "diff": {"files": files, "added": files, "removed": 0, "paths": list(paths)}}
        return {**run, **changes}

    def test_control_runs_are_counted_not_scored(self):
        runs = [self.control(), self.control(files=0, paths=()),
                self.control(files=0, paths=()), self.control(regression_pass=False)]
        row = self.row(runs)
        self.assertTrue(row["control"])
        self.assertEqual(row["outcomes"], {"error": 0, "changed nothing": 2,
                                           "changed tests only": 0, "changed app code": 1,
                                           "regression fails": 1})
        self.assertIsNone(row["success"])
        self.assertIsNone(row["interval"])
        self.assertIsNone(row["cost_per_success"])
        # Even a run that somehow lists a fix is never a success.
        self.assertFalse(report.success({**result(), "control": True}))

    def test_a_control_run_the_rig_could_not_observe_is_an_error_only(self):
        # Each would otherwise count as "changed nothing" or "regression fails".
        cases = {
            "agent error": self.control(files=0, paths=(), error="unreadable agent output"),
            "timeout": self.control(files=0, paths=(), timed_out=True),
            "diff did not apply": self.control(error="diff did not apply: x",
                                               regression_pass=False, tests={}),
            "no score": self.control(files=0, paths=(), tests={}),
        }
        for name, run in cases.items():
            with self.subTest(name):
                self.assertEqual(report.control_outcome(run), "error")
        row = self.row(list(cases.values()) + [self.control(files=0, paths=())])
        self.assertEqual(row["outcomes"]["error"], 4)
        self.assertEqual(row["outcomes"]["changed nothing"], 1)
        self.assertEqual(row["outcomes"]["regression fails"], 0)

    def test_a_control_change_to_test_files_only_is_its_own_count(self):
        cases = {
            ("wger/manager/tests/test_log.py",): "changed tests only",
            ("tests/unit/test_a.py", "src/__tests__/a.test.js"): "changed tests only",
            ("wger/manager/tests/test_log.py", "wger/manager/api/views.py"): "changed app code",
            # A file named like a test, outside a test folder, is app code.
            ("wger/test_settings.py",): "changed app code",
        }
        for paths, outcome in cases.items():
            with self.subTest(paths=paths):
                run = self.control(files=len(paths), paths=paths)
                self.assertEqual(report.control_outcome(run), outcome)
        # A result from before the rig recorded paths counts as app code.
        old = self.control()
        del old["diff"]["paths"]
        self.assertEqual(report.control_outcome(old), "changed app code")

    def test_control_rates_are_over_runs_without_an_error(self):
        runs = [self.control(), self.control(), self.control(),
                self.control(files=0, paths=(), timed_out=True)]
        row = self.row(runs)
        self.assertEqual(row["outcome_intervals"]["changed app code"], report.wilson(3, 3))
        self.assertEqual(row["outcome_intervals"]["changed nothing"], report.wilson(0, 3))
        self.assertNotIn("error", row["outcome_intervals"])
        # A cell of errors only has no rate.
        row = self.row([self.control(error="crash")])
        self.assertIsNone(row["outcome_intervals"]["changed nothing"])

    def test_control_table_says_which_prompt_measures_false_positives(self):
        with tempfile.TemporaryDirectory() as folder:
            for number, run in enumerate([self.control(), self.control(error="crash"),
                                          self.control(files=0, paths=())], 1):
                path = Path(folder) / "runs" / f"r{number}" / "result.json"
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps({**run, "run_id": f"r{number}", "choice": "",
                                            "costs": {"copilot": {"unit": "credits"}}}))
            text = report.markdown(folder)
        self.assertIn("Only the `security` prompt measures false positives", text)
        self.assertIn("For `open` and `ddd`, a safe change is the correct answer.", text)
        self.assertIn("Fisher's exact test", text)
        self.assertIn("| c | open | 3 | 1 | 1/2 (9% to 91%) | 0/2 (0% to 66%) | "
                      "1/2 (9% to 91%) | 0/2 (0% to 66%) |", text)
        self.assertNotIn("Success means", text)

    def test_three_of_three_has_a_wide_interval(self):
        low, high = report.wilson(3, 3)
        self.assertAlmostEqual(low, 0.438, places=3)
        self.assertEqual(high, 1.0)
        self.assertIsNone(report.wilson(0, 0))


def fake_tree(root, batches, triage_files, cells=("c",)):
    """A tiny checkout under `root`: a matrix with `cells`, one batch
    folder per {batch: [result, ...]}, and a triage.toml per
    {scenario: text}. Returns `root`."""
    root = Path(root)
    (root / "config").mkdir(parents=True)
    (root / "config" / "matrix.toml").write_text("".join(
        f'[[cells]]\nname = "{c}"\nharness = "claude"\nmodel = "m"\n' for c in cells))
    for name, runs in batches.items():
        for run_result in runs:
            path = root / "results" / name / "runs" / run_result["run_id"] / "result.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(run_result))
    for scenario, text in triage_files.items():
        (root / "scenarios" / scenario).mkdir(parents=True)
        (root / "scenarios" / scenario / "triage.toml").write_text(text)
    return root


def scored(run_id, scenario="app", cell="c", fixed=(), regression_pass=True, **changes):
    return {**result(cell=cell, fixed=fixed), "run_id": run_id, "scenario": scenario,
            "regression_pass": regression_pass, **changes}


def find(id, status, runs, summary="A hole.", evidence="abc1234", **extra):
    lines = [f'[[finds]]\nid = "{id}"\nstatus = "{status}"\nevidence = "{evidence}"\n'
             f'summary = "{summary}"\nruns = {json.dumps(runs)}\n']
    lines += [f'{key} = "{value}"\n' for key, value in extra.items()]
    return "".join(lines) + "\n"


HELD = {"held_since": "2026-10-24"}


class TriageTest(unittest.TestCase):
    """A triage record lists real holes the scenario did not plant (decision 13)."""
    B = "20261024T000000Z-app"

    def tree(self, folder, text):
        runs = [scored("r1"), scored("r2", regression_pass=False), scored("r3", error="crash")]
        return fake_tree(folder, {self.B: runs}, {"app": text})

    def test_a_valid_record_loads_and_only_real_finds_confirm(self):
        from rig import triage
        text = (find("F1", "fixed-upstream", [f"{self.B}/r1", f"{self.B}/r2", f"{self.B}/r3"])
                + find("F2", "open-held", [f"{self.B}/r1"], summary="",
                       evidence="private report pending", **HELD)
                + find("F3", "not-a-bug", [f"{self.B}/r1"], evidence="code read"))
        with tempfile.TemporaryDirectory() as folder:
            root = self.tree(folder, text)
            finds = triage.load("app", root)
            runs = {r["run_id"]: r for r in report.load(root / "results" / self.B)}
        self.assertEqual([f["id"] for f in finds], ["F1", "F2", "F3"])
        # A not-a-bug find never confirms; a broken regression set or an
        # agent error takes the run out, as for a planted success.
        self.assertEqual(triage.confirmed(runs["r1"], self.B, finds), ["F1", "F2"])
        self.assertEqual(triage.confirmed(runs["r2"], self.B, finds), [])
        self.assertEqual(triage.confirmed(runs["r3"], self.B, finds), [])
        # The same run in another batch is another run.
        self.assertEqual(triage.confirmed(runs["r1"], "20261025T000000Z-app", finds), [])

    def test_no_triage_file_is_no_finds(self):
        from rig import triage
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(triage.load("app", fake_tree(folder, {}, {})), [])

    def test_a_held_find_carries_no_description(self):
        from rig import triage
        with tempfile.TemporaryDirectory() as folder:
            root = self.tree(folder, find("F1", "open-held", [f"{self.B}/r1"],
                                          summary="The delete route skips the owner check.",
                                          evidence="private report pending", **HELD))
            self.assertEqual(triage.problems("app", root), [
                "find F1: an open-held find has an empty summary until it is "
                "disclosed or 90 days pass"])
            with self.assertRaises(SystemExit):
                triage.load("app", root)

    def test_bad_records_are_refused(self):
        from rig import triage
        run = [f"{self.B}/r1"]
        cases = {
            "status 'wontfix' is not one of": find("F1", "wontfix", run),
            "evidence is an opaque note": find("F1", "open-held", run, summary="",
                                               evidence="owner check missing", **HELD),
            "needs held_since": find("F1", "open-held", run, summary="",
                                     evidence="not reported"),
            "only an open-held find has held_since": find("F1", "disclosed", run, **HELD),
            "names an upstream commit or a GHSA id": find("F1", "fixed-upstream", run,
                                                          evidence="fixed later"),
            "needs a summary": find("F1", "not-a-bug", run, summary=""),
            "no result for run": find("F1", "disclosed", [f"{self.B}/r9"]),
            "is not '<batch>/<run_id>' of app": find(
                "F1", "disclosed", ["20261024T000000Z-other/r1"]),
            "lists no runs": find("F1", "disclosed", []),
            "lists a run twice": find("F1", "disclosed", run + run),
            "id must be short and opaque": find("session-delete", "disclosed", run),
            "id used twice": find("F1", "disclosed", run) + find("F1", "hardening", run),
            "unknown keys ['summmary']": find("F1", "disclosed", run, summmary="x"),
        }
        for expected, text in cases.items():
            with self.subTest(expected), tempfile.TemporaryDirectory() as folder:
                found = triage.problems("app", self.tree(folder, text))
                self.assertTrue(any(expected in p for p in found), found)
        # A GHSA id is upstream evidence too.
        with tempfile.TemporaryDirectory() as folder:
            root = self.tree(folder, find("F1", "disclosed", run,
                                          evidence="GHSA-2222-3333-4444"))
            self.assertEqual(triage.problems("app", root), [])

    def test_every_triage_file_in_the_repo_is_valid(self):
        from rig import triage
        names = sorted(p.parent.name for p in ROOT.glob("scenarios/*/triage.toml"))
        for name in names:
            with self.subTest(scenario=name):
                self.assertEqual(triage.problems(name), [])


def load_scoreboard():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "scoreboard", ROOT / "scripts" / "scoreboard.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ScoreboardTest(unittest.TestCase):
    def test_second_table_counts_planted_successes_and_confirmed_finds(self):
        planted, control = "20261024T000000Z-app", "20261024T010000Z-ctl"
        batches = {
            planted: [
                scored("a1", fixed=("s1",)),             # planted success
                scored("a2", fixed=("s1",)),             # success and a find: planted
                scored("a3"),                            # confirmed find only
                scored("a4", regression_pass=False),     # find, but broke the set
                scored("a5"),                            # not-a-bug find
                scored("a6"),                            # nothing
                scored("b1", cell="d"),                  # confirmed find, cell d
            ],
            control: [scored("k1", scenario="ctl", control=True),
                      scored("k2", scenario="ctl", control=True)],
        }
        files = {
            "app": find("F1", "fixed-upstream", [f"{planted}/a2", f"{planted}/a3",
                                                 f"{planted}/a4", f"{planted}/b1"])
            + find("F2", "not-a-bug", [f"{planted}/a5"]),
            "ctl": find("W1", "open-held", [f"{control}/k1"], summary="",
                        evidence="not reported", **HELD),
        }
        board = load_scoreboard()
        with tempfile.TemporaryDirectory() as folder:
            root = fake_tree(folder, batches, files, cells=("c", "d"))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                board.main([], root=root)
        text = out.getvalue()
        first, second = text.split("Planted successes and confirmed finds")
        # The first table stays as it was: planted successes, no controls.
        self.assertIn("| app | 2/6 | 0/1 |", first)
        self.assertNotIn("ctl", first)
        # c: 8 runs (6 planted, 2 control). 2 planted successes; a3 and k1
        # are confirmed finds. a2 counts as planted only, a4 broke the
        # regression set, and a5's find is not a bug.
        self.assertIn(f"| c | 8 | 2/8 ({report._interval(report.wilson(2, 8))}) | "
                      f"2/8 ({report._interval(report.wilson(2, 8))}) | "
                      f"4/8 ({report._interval(report.wilson(4, 8))}) |", second)
        self.assertIn("| d | 1 | 0/1 (0% to 79%) | 1/1 (21% to 100%) | "
                      "1/1 (21% to 100%) |", second)
        # Per scenario: runs with a confirmed find, distinct finds, held finds.
        self.assertIn("| app | 7 | yes | 3 | 1 | 0 |", second)
        self.assertIn("| ctl | 2 | yes | 1 | 1 | 1 |", second)
        self.assertIn("lower bound", second)

    def test_one_unpriced_run_makes_the_cell_cost_unknown(self):
        # The same rule as the batch report: no partial sum read as the whole.
        board = load_scoreboard()
        sheet = ReportTest.SHEETS["s"]
        newest = {("app", "c"): ("b", [scored("a1", fixed=("s1",)),
                                       scored("a2", fixed=("s1",), by_model={"x": {}})]),
                  ("app", "d"): ("b", [scored("b1", cell="d", fixed=("s1",))])}
        lines = board.planted_table(newest, ["c", "d"], sheet)
        self.assertIn("| Credits per success | n/a | 10 |", lines)

    def test_a_bad_triage_file_stops_the_scoreboard(self):
        batch = "20261024T000000Z-app"
        board = load_scoreboard()
        with tempfile.TemporaryDirectory() as folder:
            root = fake_tree(folder, {batch: [scored("a1")]},
                             {"app": find("F1", "open-held", [f"{batch}/a1"],
                                          evidence="private report pending", **HELD)})
            with self.assertRaises(SystemExit), contextlib.redirect_stdout(io.StringIO()):
                board.main([], root=root)


class CutoffTest(unittest.TestCase):
    def test_fix_after_cutoff_compares_months(self):
        cases = {("2026-05-08", "2026-01"): True,
                 # The fix month itself counts as known: the model may have seen it.
                 ("2026-05-08", "2026-05"): False,
                 ("2026-05-08", "2026-09"): False,
                 (None, "2026-01"): None,
                 ("2026-05-08", None): None}
        for (fix, cutoff), expected in cases.items():
            with self.subTest(fix=fix, cutoff=cutoff):
                self.assertIs(run.fix_after_cutoff(fix, cutoff), expected)

    def test_run_warns_and_records_but_does_not_refuse(self):
        import dataclasses
        from unittest import mock

        from rig import scenario as scenarios
        real = scenarios.load("booking-ladder")
        dated = dataclasses.replace(real, fix_date="2026-05-08")
        matrix = json.loads(json.dumps(MATRIX))
        base = next(c for c in matrix["cells"] if c["name"] == "fake-none")
        matrix["cells"] += [{**base, "name": "fake-late", "cutoff": "2026-06"},
                            {**base, "name": "fake-early", "cutoff": "2026-01"}]
        said = []
        with mock.patch("rig.run.scenarios.load", return_value=dated):
            out, rows = run.run_batch(
                "booking-ladder", matrix, ["fake-late", "fake-early", "fake-none"],
                ["open"], 1, results_root=tempfile.mkdtemp(prefix="model-rig-results-"),
                echo=said.append)
        warnings = [line for line in said if line.startswith("WARNING")]
        self.assertEqual(len(warnings), 1)
        self.assertIn("fake-late", warnings[0])
        self.assertEqual([r["fix_after_cutoff"] for r in rows], [False, True, None])
        text = report.markdown(out)
        self.assertIn("Fix after cutoff |", text)
        self.assertRegex(text, r"\| fake-late \| open \|.*\| no \|\n")
        self.assertRegex(text, r"\| fake-early \| open \|.*\| yes \|\n")
        self.assertRegex(text, r"\| fake-none \| open \|.*\| unknown \|\n")


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
        self.assertEqual(invocation.env["DISABLE_TELEMETRY"], "1")

    def test_hosts_come_from_network_config(self):
        import tomllib
        lists = tomllib.loads((ROOT / "config" / "network.toml").read_text())["hosts"]
        for cell in run.load_matrix()["cells"]:
            with self.subTest(cell=cell["name"]):
                self.assertTrue(cell["hosts"])
                self.assertEqual(cell["hosts"], lists[cell["harness"]])
        self.assertTrue(all(not c["hosts"] for c in MATRIX["cells"]))


class _EchoHandler(socketserver.BaseRequestHandler):
    def handle(self):
        while data := self.request.recv(4096):
            self.request.sendall(data)


@contextlib.contextmanager
def echo_server():
    """A TCP echo server on 127.0.0.1, standing in for a provider host.
    Yields its "host:port"."""
    server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), _EchoHandler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


def ask_proxy(path, request):
    """Send one request head to the proxy socket. Return the socket and
    the reply head."""
    client = socket.socket(socket.AF_UNIX)
    client.settimeout(5)
    client.connect(str(path))
    client.sendall(request.encode())
    head = b""
    while b"\r\n\r\n" not in head:
        chunk = client.recv(1)
        if not chunk:
            break
        head += chunk
    return client, head.decode()


class ProxyTest(unittest.TestCase):
    def test_allowed_host_tunnels_and_others_get_403(self):
        with echo_server() as echo, tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / "network.jsonl"
            with proxy.serve([echo], log) as gate:
                client, head = ask_proxy(gate.socket, f"CONNECT {echo} HTTP/1.1\r\n\r\n")
                self.assertTrue(head.startswith("HTTP/1.1 200"), head)
                client.sendall(b"ping")
                self.assertEqual(client.recv(4), b"ping")
                client.close()
                denied, head = ask_proxy(
                    gate.socket, "CONNECT github.com:443 HTTP/1.1\r\n\r\n")
                self.assertTrue(head.startswith("HTTP/1.1 403"), head)
                self.assertEqual(denied.recv(1), b"")
                denied.close()
                # A plain proxied GET is not a CONNECT, so it is refused too.
                plain, head = ask_proxy(
                    gate.socket, "GET http://example.com/ HTTP/1.1\r\n\r\n")
                self.assertTrue(head.startswith("HTTP/1.1 403"), head)
                plain.close()
            lines = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertFalse(Path(gate.socket).exists())
            summary = proxy.summary(log)
        host, port = echo.split(":")
        self.assertEqual([(l["host"], l["port"], l["allowed"]) for l in lines],
                         [(host, int(port), True), ("github.com", 443, False),
                          ("example.com", 80, False)])
        self.assertTrue(all("time" in line for line in lines))
        self.assertEqual(summary, {"allowed": [host],
                                              "denied": ["example.com", "github.com"]})

    def test_allow_rule(self):
        hosts = ["api.anthropic.com", "*.example.com", "127.0.0.1:8080"]
        cases = {
            ("api.anthropic.com", 443): True,
            ("API.Anthropic.com.", 443): True,
            ("api.anthropic.com", 80): False,   # a bare host means port 443
            ("api.anthropic.com.evil.test", 443): False,
            ("evil.api.anthropic.com", 443): False,  # no wildcard, no subdomain
            ("a.b.example.com", 443): True,
            ("example.com", 443): False,        # "*." matches subdomains only
            ("badexample.com", 443): False,
            ("127.0.0.1", 8080): True,
            ("127.0.0.1", 443): False,
        }
        for (host, port), expected in cases.items():
            with self.subTest(host=host, port=port):
                self.assertIs(proxy.allowed(host, port, hosts), expected)


class GuardTest(unittest.TestCase):
    def test_real_runs_need_yes(self):
        with contextlib.redirect_stdout(io.StringIO()) as said:
            code = main(["run", "booking-ladder", "--cells", "claude-opus-medium",
                         "--prompts", "open", "--repeats", "1"])
        self.assertEqual(code, 2)
        self.assertIn("--yes", said.getvalue())


if __name__ == "__main__":
    unittest.main()
