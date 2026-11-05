"""Installed release observations and runtime-resolution inventory guard."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import check_releases as checker


class ReleaseCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in checker.INVENTORIES:
            self.save(name, {})

    def save(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(content))

    def test_pin_guard_reports_nested_and_empty_fields(self):
        self.save('hermes/manifest.json', {'plugins': [{'commit': None, 'version': ''}],
                                         'omh': {'reference_commit': 'abc'}})
        self.save('codex/inventories/external-skills.json', {'skills': {
            'demo': {'ref': 'main', 'releaseTag': None, 'skillFolderHash': 'abc'}}})
        pins = checker.inventory_pins(self.root)
        self.assertEqual(len(pins), 6)
        self.assertIn('hermes/manifest.json.plugins[0].commit', pins)
        self.assertIn('codex/inventories/external-skills.json.skills.demo.ref', pins)

    def test_unpinned_inventory_accepts_repo_names_and_schema_versions(self):
        self.save('codex/inventories/tools.lock.json', {'schema_version': 1,
                  'omh': {'source': 'https://github.com/o/r', 'runtime_installed': False}})
        self.assertEqual(checker.inventory_pins(self.root), [])

    def test_status_preserves_git_distance_and_prerelease_suffixes(self):
        for installed, tag, status in [('4.0.6', 'v4.0.6', 'current'),
                                       ('v0.2.1', 'v0.3.1', 'different'),
                                       ('v0.3.1-2-gabcdef', 'v0.3.1', 'different'),
                                       ('4.0.6-rc1', 'v4.0.6', 'different'),
                                       (None, 'v4.0.6', 'unknown'), ('1.0.0', None, 'no_release')]:
            with self.subTest(installed=installed):
                self.assertEqual(checker.release_status(installed, tag), status)

    def test_omh_reads_active_state_then_cli_fallback(self):
        self.save('.local/share/omh/self-update.json', {'active': {'version': '4.0.6'}})
        with patch.object(checker, 'command_output') as command:
            self.assertEqual(checker.omh_version(self.root)[0], '4.0.6')
        command.assert_not_called()
        self.save('.local/share/omh/self-update.json', {'active': {'version': ''}})
        with patch.object(checker, 'command_output', return_value=('omh 4.0.7 (build)', None)) as command:
            self.assertEqual(checker.omh_version(self.root)[0], '4.0.7')
        command.assert_called_once_with('omh', '--version')

    def test_skill_copy_requires_matching_bundles_for_provenance(self):
        source = self.root / 'shared/skills/omh/omh-demo'
        source.mkdir(parents=True)
        (source / 'SKILL.md').write_text('demo')
        home = self.root / 'home/skills'
        observation = checker.installed_skill_copy(self.root, home, {'version': '4.0.6'})
        self.assertIsNone(observation['installed'])
        self.assertEqual(observation['copy_status'], 'missing')
        (home / 'omh-demo').mkdir(parents=True)
        (home / 'omh-demo/SKILL.md').write_text('demo')
        self.assertEqual(checker.installed_skill_copy(self.root, home, {'version': '4.0.6'})['installed'], '4.0.6')
        (home / 'omh-demo/SKILL.md').write_text('personal edit')
        self.assertEqual(checker.installed_skill_copy(self.root, home, {'version': '4.0.6'})['copy_status'], 'mixed')

    def rows(self):
        return [{'component': name, 'repo': 'o/r', 'installed': '1.0.0',
                 **({'patch_target': name} if name == 'hermes-agent' else {})}
                for name in ['hermes-agent', 'copy']]

    def test_latest_lookup_cached_and_tag_patch_reported(self):
        target = self.root / 'hermes/patches/hermes-agent/v2.0.0.patch'
        target.parent.mkdir(parents=True)
        target.write_text('patch')
        with patch.object(checker, 'installed_components', return_value=self.rows()), \
             patch.object(checker, 'latest_release', return_value='v2.0.0') as latest:
            result = checker.report(self.root)
        latest.assert_called_once_with('o/r')
        self.assertTrue(result['components'][0]['latest_patch_exists'])
        self.assertEqual(result['components'][0]['status'], 'different')
        target.unlink()
        with patch.object(checker, 'installed_components', return_value=self.rows()), \
             patch.object(checker, 'latest_release', return_value='v2.0.0'):
            self.assertFalse(checker.report(self.root)['components'][0]['latest_patch_exists'])

    def test_lookup_failure_has_explicit_error(self):
        with patch.object(checker, 'installed_components', return_value=self.rows()), \
             patch.object(checker, 'latest_release', side_effect=OSError('offline')):
            result = checker.report(self.root)
        self.assertEqual(result['components'][0]['status'], 'error')
        self.assertEqual(result['components'][0]['release_error'], 'offline')

    def test_cli_fails_for_pins_and_lookup_errors_but_reports_updates(self):
        for pins, row, expected in [([], {'status': 'different'}, 0),
                                    (['manifest.commit'], {'status': 'current'}, 1),
                                    ([], {'status': 'error'}, 1),
                                    ([], {'status': 'unknown', 'observation_error': 'missing'}, 1)]:
            with self.subTest(pins=pins, row=row), \
                 patch.object(checker, 'report', return_value={'inventory_pins': pins, 'components': [row]}), \
                 redirect_stdout(StringIO()) as output:
                self.assertEqual(checker.main(['--json']), expected)
                self.assertEqual(json.loads(output.getvalue())['inventory_pins'], pins)

    def test_installed_components_reads_cli_git_and_both_skill_homes(self):
        self.save('hermes/manifest.json', {'upstream': {'repo': 'https://github.com/o/hermes'},
                  'omh': {'repo': 'https://github.com/o/omh'},
                  'plugins': [{'name': 'provider-usage', 'repo': 'https://github.com/o/plugin'}]})
        self.save('shared/skills/omh/SOURCE.json', {'version': '4.0.6', 'upstream': 'https://github.com/o/omh'})
        with patch.object(checker, 'command_output', side_effect=[('Hermes Agent v0.22.7 (date)', None),
                          ('omh 4.0.6 (build)', None), ('v0.2.1', None)]) as command, \
             patch.dict('os.environ', {}, clear=True):
            rows = checker.installed_components(self.root, self.root)
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0]['installed'], '0.22.7')
        self.assertEqual(rows[2]['installed'], 'v0.2.1')
        self.assertEqual(rows[-2]['evidence'], str(self.root / '.claude/skills'))
        self.assertEqual(rows[-1]['evidence'], str(self.root / '.agents/skills'))
        self.assertEqual(command.call_args_list[-1].args,
                         ('git', '-C', str(self.root / '.hermes/plugins/provider-usage'), 'describe', '--tags', '--always'))


if __name__ == '__main__':
    unittest.main()
