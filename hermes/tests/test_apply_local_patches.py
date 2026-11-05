"""Local patch sets: report and apply on top of an official release checkout."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import apply_local_patches as alp  # noqa: E402


def git(repo, *args):
    subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True)


class LocalPatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.repo = base / 'checkout'
        self.repo.mkdir()
        git(self.repo, 'init', '-q')
        git(self.repo, 'config', 'user.email', 't@example.invalid')
        git(self.repo, 'config', 'user.name', 't')
        (self.repo / 'a.txt').write_text('one\n')
        git(self.repo, 'add', 'a.txt')
        git(self.repo, 'commit', '-qm', 'base')
        git(self.repo, 'tag', 'v1.0.0')
        self.patches = base / 'patches'
        (self.patches / 'demo').mkdir(parents=True)
        (self.repo / 'a.txt').write_text('one\ntwo\n')
        diff = subprocess.run(['git', '-C', str(self.repo), 'diff'], capture_output=True, text=True).stdout
        (self.patches / 'demo' / 'v1.0.0.patch').write_text(diff)
        git(self.repo, 'checkout', '-q', 'a.txt')
        self.old = alp.PATCHES
        alp.PATCHES = self.patches

    def tearDown(self):
        alp.PATCHES = self.old
        self.temp.cleanup()

    def test_applicable_then_applied(self):
        self.assertEqual(alp.status('demo', self.repo)['status'], 'applicable')
        git(self.repo, 'apply', str(self.patches / 'demo' / 'v1.0.0.patch'))
        self.assertEqual(alp.status('demo', self.repo)['status'], 'applied')

    def test_conflict_and_missing_patch(self):
        (self.repo / 'a.txt').write_text('changed upstream\n')
        self.assertEqual(alp.status('demo', self.repo)['status'], 'conflict')
        git(self.repo, 'checkout', '-q', 'a.txt')
        git(self.repo, 'tag', '-d', 'v1.0.0')
        git(self.repo, 'tag', 'v2.0.0')
        row = alp.status('demo', self.repo)
        self.assertEqual(row['status'], 'no_patch')
        self.assertEqual(row['available'], ['v1.0.0'])

    def run_apply(self):
        home = Path(self.temp.name) / 'home'
        home.mkdir(exist_ok=True)
        old_targets = alp.targets
        alp.targets = lambda _home: {'demo': self.repo}
        old_argv = sys.argv
        sys.argv = ['apply_local_patches.py', '--home', str(home), '--apply']
        try:
            from io import StringIO
            from contextlib import redirect_stdout
            out = StringIO()
            with redirect_stdout(out):
                code = alp.main()
            return code, json.loads(out.getvalue())[0]
        finally:
            alp.targets = old_targets
            sys.argv = old_argv

    def stash_list(self):
        return subprocess.run(['git', '-C', str(self.repo), 'stash', 'list'],
                              capture_output=True, text=True).stdout

    def test_restored_older_edits_are_replaced_by_the_tag_patch(self):
        # hermes update restored the previous release's slightly different edits
        (self.repo / 'a.txt').write_text('one\ntwo (old wording)\n')
        (self.repo / 'new.txt').write_text('untracked from old edits\n')
        self.assertEqual(alp.status('demo', self.repo)['status'], 'conflict')
        code, row = self.run_apply()
        self.assertEqual(code, 0)
        self.assertEqual(row['status'], 'applied')
        self.assertEqual((self.repo / 'a.txt').read_text(), 'one\ntwo\n')
        self.assertIn('agent-setup-before-v1.0.0-patch', self.stash_list())

    def test_patch_that_does_not_fit_the_release_keeps_current_edits(self):
        git(self.repo, 'tag', '-d', 'v1.0.0')
        (self.repo / 'a.txt').write_text('upstream rewrote this\n')
        git(self.repo, 'commit', '-qam', 'upstream')
        git(self.repo, 'tag', 'v1.0.0')
        (self.repo / 'a.txt').write_text('upstream rewrote this\nmine\n')
        code, row = self.run_apply()
        self.assertEqual(code, 1)
        self.assertEqual(row['status'], 'conflict')
        self.assertEqual((self.repo / 'a.txt').read_text(), 'upstream rewrote this\nmine\n')
        self.assertEqual(self.stash_list(), '')


if __name__ == '__main__':
    unittest.main()
