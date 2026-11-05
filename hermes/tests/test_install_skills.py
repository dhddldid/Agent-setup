import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, call

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('installer', ROOT / 'scripts/install_skills.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def setUp(self):
        (ROOT / '.local').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / '.local')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / 'source'
        self.home = self.base / 'home'
        (self.source / 'skills/demo/scripts').mkdir(parents=True)
        (self.source / 'skills/demo/SKILL.md').write_text('---\nname: demo\ndescription: Test.\n---\nBody.\n')
        (self.source / 'skills/demo/scripts/helper.py').write_text('print("demo")\n')
        (self.source / 'LICENSE').write_text('fixture license')
        self.manifest = {'skills': [{'name': 'demo', 'source_kind': 'upstream', 'source_path': 'skills/demo', 'install_path': 'skills/test/demo'}]}

    def apply(self, apply=True):
        return installer.install(self.manifest, self.home, self.source, apply)

    def checkout_manifest(self):
        return {'upstream': {'repo': 'https://github.com/owner/upstream.git'}}

    def test_checkout_preview_resolves_latest_without_writes(self):
        path = self.base / 'new-checkout'
        with patch.object(installer, 'latest_release', return_value='v9.8.7') as latest, \
             patch.object(installer, 'tag_commit', return_value='a' * 40) as commit, \
             patch.object(installer, 'run') as run:
            self.assertIsNone(installer.source_checkout(self.checkout_manifest(), path, False))
        latest.assert_called_once_with('owner/upstream')
        commit.assert_called_once_with('owner/upstream', 'v9.8.7')
        run.assert_not_called()
        self.assertFalse(path.exists())

    def test_checkout_apply_fetches_resolved_stable_tag(self):
        path = self.base / 'new-checkout'
        with patch.object(installer, 'latest_release', return_value='v9.8.7'), \
             patch.object(installer, 'tag_commit', return_value='a' * 40), \
             patch.object(installer, 'run', return_value='a' * 40) as run:
            self.assertEqual(installer.source_checkout(self.checkout_manifest(), path, True), path)
        self.assertIn(call('git', '-C', str(path), 'fetch', '--depth=1',
                           'https://github.com/owner/upstream.git', 'refs/tags/v9.8.7'), run.call_args_list)
        self.assertEqual(run.call_args_list[-1], call('git', '-C', str(path), 'checkout', '--detach', 'a' * 40))

    def test_checkout_existing_old_release_preview_needs_source(self):
        with patch.object(installer, 'latest_release', return_value='v9.8.7'), \
             patch.object(installer, 'tag_commit', return_value='a' * 40), \
             patch.object(installer, 'run', return_value='b' * 40):
            self.assertIsNone(installer.source_checkout(self.checkout_manifest(), self.source, False))

    def test_checkout_existing_current_release_is_reused(self):
        with patch.object(installer, 'latest_release', return_value='v9.8.7'), \
             patch.object(installer, 'tag_commit', return_value='a' * 40), \
             patch.object(installer, 'run', return_value='a' * 40) as run:
            self.assertEqual(installer.source_checkout(self.checkout_manifest(), self.source, True), self.source)
        self.assertFalse(any('fetch' in args.args for args in run.call_args_list))

    def test_checkout_no_release_fails_before_write(self):
        with patch.object(installer, 'latest_release', return_value=None), \
             patch.object(installer, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'No stable'):
                installer.source_checkout(self.checkout_manifest(), self.base / 'new', True)
        run.assert_not_called()

    def test_checkout_changed_release_fails_before_checkout(self):
        with patch.object(installer, 'latest_release', return_value='v9.8.7'), \
             patch.object(installer, 'tag_commit', return_value='a' * 40), \
             patch.object(installer, 'run', return_value='b' * 40) as run:
            with self.assertRaisesRegex(ValueError, 'changed during resolution'):
                installer.source_checkout(self.checkout_manifest(), self.base / 'new', True)
        self.assertFalse(any('checkout' in args.args for args in run.call_args_list))

    def test_preview_does_not_write(self):
        self.assertEqual(self.apply(False)[0]['status'], 'add')
        self.assertFalse(self.home.exists())

    def test_install_supporting_files_and_license(self):
        self.apply()
        self.assertEqual((self.home / 'skills/test/demo/scripts/helper.py').read_text(), 'print("demo")\n')
        self.assertEqual((self.home / 'skills/test/demo/_UPSTREAM_LICENSE').read_text(), 'fixture license')

    def test_repeat_is_unchanged(self):
        self.apply()
        self.assertEqual(self.apply()[0]['status'], 'unchanged')

    def test_conflict_preserves_existing(self):
        self.apply()
        target = self.home / 'skills/test/demo/SKILL.md'
        target.write_text('---\nname: demo\n---\nPersonal edit.\n')
        with self.assertRaises(ValueError):
            self.apply()
        self.assertIn('Personal edit.', target.read_text())

    def test_existing_name_other_category(self):
        destination = self.home / 'skills/other/demo'
        destination.mkdir(parents=True)
        (destination / 'SKILL.md').write_text('---\nname: demo\n---\nPersonal edit.\n')
        with self.assertRaises(ValueError):
            self.apply()
        self.assertFalse((self.home / 'skills/test/demo').exists())

    def test_manifest_traversal(self):
        self.manifest['skills'][0]['install_path'] = '../escape'
        with self.assertRaises(ValueError):
            self.apply()
        self.assertFalse(self.home.exists())

    def test_source_symlink_refused(self):
        (self.source / 'skills/demo/unsafe').symlink_to(self.source / 'LICENSE')
        with self.assertRaises(ValueError):
            self.apply()
        self.assertFalse(self.home.exists())

    def test_target_symlink_refused(self):
        self.home.mkdir()
        (self.home / 'skills').symlink_to(self.source)
        with self.assertRaises(ValueError):
            self.apply()

    def test_duplicate_manifest(self):
        self.manifest['skills'].append(dict(self.manifest['skills'][0]))
        with self.assertRaises(ValueError):
            self.apply()


if __name__ == '__main__':
    unittest.main()
