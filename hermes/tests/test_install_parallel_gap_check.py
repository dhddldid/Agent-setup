import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("install_parallel", Path(__file__).resolve().parents[1] / "scripts/install_parallel_gap_check.py")
assert SPEC is not None and SPEC.loader is not None
install = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(install)


class InstallParallelGapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "hermes"

    def test_default_dry_run_writes_nothing(self):
        with patch.object(install.subprocess, "run") as run, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(install.main(["--home", str(self.home), "--json"]), 0)
        self.assertFalse(self.home.exists())
        run.assert_not_called()
        result = json.loads(output.getvalue())
        self.assertEqual(result["mode"], "dry-run")
        self.assertEqual(result["schedule"], "every 72h")
        self.assertEqual(result["llm_cost"], 0)
        self.assertIn("--no-agent", result["command"])
        self.assertIn("--catch-up", result["command"])

    def test_wrapper_executes_both_reports_and_only_findings(self):
        repo = self.root / "repo"
        scripts = repo / "scripts"
        scripts.mkdir(parents=True)
        checker = scripts / "check_parallel_gaps.py"
        checker.write_text("import pathlib,sys\np=pathlib.Path(sys.argv[sys.argv.index('--report-file')+1]); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(sys.argv[1]); print('누락 발견') if sys.argv[1]=='routing' else None\nsys.exit(1 if sys.argv[1]=='routing' else 0)\n")
        wrapper = self.root / "job.py"
        wrapper.write_text(install.wrapper(repo, self.home, Path(sys.executable)))
        result = subprocess.run([sys.executable, str(wrapper)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "누락 발견\n")
        reports = list((self.home / "reports/parallel-gaps").glob("*.md"))
        self.assertEqual(len(reports), 2)
        self.assertEqual({p.read_text() for p in reports}, {"history", "routing"})

    def test_wrapper_clean_silent_and_errors_surface(self):
        namespace: dict = {"__name__": "test_wrapper"}
        exec(install.wrapper(self.root, self.home, Path(sys.executable)), namespace)
        with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "", "")), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(namespace["main"](), 0)
        self.assertEqual(output.getvalue(), "")
        with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 2, "", "DB missing")), contextlib.redirect_stderr(io.StringIO()) as error:
            self.assertEqual(namespace["main"](), 2)
        self.assertIn("DB missing", error.getvalue())

    def test_existing_job_rejected_before_writes(self):
        cron = self.home / "cron"
        cron.mkdir(parents=True)
        (cron / "jobs.json").write_text(json.dumps({"jobs": [{"name": install.NAME}]}))
        with patch.object(install.subprocess, "run") as run, contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            install.main(["--apply", "--home", str(self.home)])
        run.assert_not_called()
        self.assertFalse((self.home / "scripts").exists())


if __name__ == "__main__":
    unittest.main()
