"""The management checker must select only the requested executor."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CheckerTests(unittest.TestCase):
    def test_claude_selection_runs_only_native_agent_check(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/check.py"), "--executor", "claude"],
            cwd=ROOT.parent,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("25 route agents match routes/claude-code.json", result.stdout)
        self.assertIn("PASS executor: claude", result.stdout)
        self.assertNotIn("PASS executor: codex", result.stdout)
        self.assertNotIn("PASS executor: hermes", result.stdout)

    def test_unknown_executor_is_rejected(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/check.py"), "--executor", "unknown"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("PASS executor:", result.stdout)

    def test_failed_native_check_is_not_reported_as_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "scripts").mkdir()
            shutil.copy2(ROOT / "scripts/check.py", root / "scripts/check.py")
            shutil.copytree(ROOT / "claude", root / "claude")
            agent = root / "claude/.claude/agents/route-quick-fable.md"
            agent.write_text(agent.read_text() + "intentional mismatch for regression test\n")
            result = subprocess.run(
                [sys.executable, str(root / "scripts/check.py"), "--executor", "claude"],
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAIL executor: claude", result.stdout)
        self.assertNotIn("PASS executor: claude", result.stdout)


if __name__ == "__main__":
    unittest.main()
