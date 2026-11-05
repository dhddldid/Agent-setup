import importlib.util
import os
import json
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('global_rules', ROOT / 'scripts/install_global_rules.py')
assert spec is not None and spec.loader is not None
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class GlobalRulesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / 'profile'
        self.target = self.home / 'SOUL.md'

    def seed(self, content):
        self.home.mkdir(parents=True, exist_ok=True)
        self.target.write_text(content, encoding='utf-8')

    def test_browser_policy_requires_direct_repl_without_aside_agent(self):
        body = installer.browser_policy()
        for requirement in (
            'Hermes model',
            '`repl`',
            'Do not use Aside\'s own AI agent',
            '`aside exec`',
            'natural-language prompts',
            'Do not switch to `exec`',
        ):
            self.assertIn(requirement, body)
        installer.install(self.home, apply=True)
        self.assertIn(body, self.target.read_text())

    def test_preview_does_not_write(self):
        self.assertEqual(installer.install(self.home)['status'], 'add')
        self.assertFalse(self.home.exists())

    def test_first_install_and_repeat(self):
        self.assertEqual(installer.install(self.home, apply=True)['status'], 'added')
        content = self.target.read_bytes()
        self.assertEqual(installer.install(self.home, apply=True)['status'], 'unchanged')
        self.assertEqual(self.target.read_bytes(), content)
        self.assertNotIn(installer.LEGACY_REPORT_START, content.decode())
        self.assertNotIn(installer.LEGACY_REPORT_HEADING, content.decode())
        self.assertEqual(installer.install(self.home)['legacy_report_policy'], 'absent')
        self.assertEqual(content.decode().count(installer.BROWSER_START), 1)
        self.assertNotIn('hermes-setup:user-intent:begin', content.decode())
        self.assertNotIn('## User intent and course correction', content.decode())
        self.assertIn(installer.delivery_policy(), content.decode())
        self.assertEqual(content.decode().count(installer.DELIVERY_START), 1)
        self.assertIn(installer.common_policy(), content.decode())
        self.assertEqual(content.decode().count(installer.COMMON_START), 1)

    def test_common_policy_is_generated_from_shared_rules(self):
        shared = (ROOT.parent / 'shared/rules/common.md').read_text(encoding='utf-8').strip()
        self.assertEqual(installer.common_policy(), shared)
        self.assertTrue(installer.common_policy().startswith(installer.COMMON_HEADING))

    def test_preserves_existing_text(self):
        existing = '# My tone\nPersonal rules.\n'
        self.seed(existing)
        installer.install(self.home, apply=True)
        self.assertTrue(self.target.read_text().startswith(existing))

    def test_existing_unmarked_browser_policy_not_duplicated(self):
        existing = '# My tone\n\n' + installer.browser_policy() + '\n\n## Other rules\nKeep me.\n'
        self.seed(existing)
        self.assertEqual(installer.install(self.home, apply=True)['status'], 'added')
        updated = self.target.read_text()
        self.assertTrue(updated.startswith(existing))
        self.assertEqual(updated.count(installer.browser_policy()), 1)
        self.assertNotIn(installer.BROWSER_START, updated)

    def test_retired_unmarked_rule_is_preserved(self):
        retired = '## User intent and course correction\nPersonal existing rule.\n'
        existing = (installer.common_policy() + '\n\n' + installer.omh_policy() + '\n\n'
                    + installer.browser_policy() + '\n\n' + retired + '\n'
                    + installer.delivery_policy() + '\n')
        self.seed(existing)
        self.assertEqual(installer.install(self.home, apply=True)['status'], 'unchanged')
        self.assertEqual(self.target.read_text(), existing)

    def test_omh_workflow_policy_installed_once(self):
        installer.install(self.home, apply=True)
        installer.install(self.home, apply=True)
        content = self.target.read_text()
        self.assertEqual(content.count(installer.OMH_START), 1)
        body = installer.omh_policy()
        self.assertTrue(body.startswith(installer.OMH_HEADING))
        self.assertLessEqual(len(body.splitlines()), 25)
        for skill in ('dag-ulw', 'ulw-work', 'ulw-loop', 'ulw-plan', 'omh-plan',
                      'omh-verification-gate', 'omh-code-review'):
            self.assertIn(f'`{skill}`', body)
        for requirement in ('any language', 'custom and project skills', 'node and lane',
                            'Route Hint or skill shortlist', '`skill_view` before the first action',
                            'every `delegate_task`', 'omh_delegate_route', 'omh_todo',
                            'omh_agent_board', 'omh_run_summary', 'in Korean'):
            self.assertIn(requirement, body)

    def test_shipped_old_version_replaced_in_place(self):
        old = '## Previously shipped OMH\nOld rules.'
        self.seed('Personal prefix.\n' + installer.OMH_START + '\n' + old + '\n'
                  + installer.OMH_END + '\nPersonal suffix.\n')
        with patch.object(installer, 'shipped_hashes', return_value={installer.digest(old)}):
            self.assertEqual(installer.install(self.home)['status'], 'update')
            self.assertIn(old, self.target.read_text())
            self.assertEqual(installer.install(self.home, apply=True)['status'], 'updated')
        content = self.target.read_text()
        self.assertTrue(content.startswith('Personal prefix.\n' + installer.OMH_START))
        self.assertIn(installer.omh_policy(), content)
        self.assertIn(installer.OMH_END + '\nPersonal suffix.\n', content)

    def test_history_recognizes_every_committed_version(self):
        repo = Path(self.temp.name) / 'source'
        templates = repo / 'hermes/templates'
        templates.mkdir(parents=True)
        template = templates / 'omh-workflow.md'

        def git(*args):
            return subprocess.run(['git', '-C', str(repo), *args], check=True,
                                  capture_output=True, text=True)

        git('init')
        for version in ('First shipped.', 'Second shipped.', 'Third shipped.'):
            template.write_text(version + '\n', encoding='utf-8')
            git('add', '.')
            git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                'commit', '-m', 'Ship template')
        template.write_text('Uncommitted version.\n', encoding='utf-8')
        with patch.object(installer, 'ROOT', repo / 'hermes'):
            hashes = installer.shipped_hashes(template)
        for version in ('First shipped.', 'Second shipped.', 'Third shipped.'):
            self.assertIn(installer.digest(version), hashes)
        self.assertNotIn(installer.digest('Uncommitted version.'), hashes)

    def test_old_shipped_versions_replace_all_four_policies(self):
        policies = (
            (installer.COMMON_START, installer.COMMON_END, installer.common_policy()),
            (installer.OMH_START, installer.OMH_END, installer.omh_policy()),
            (installer.BROWSER_START, installer.BROWSER_END, installer.browser_policy()),
            (installer.DELIVERY_START, installer.DELIVERY_END, installer.delivery_policy()),
        )
        self.seed('\n'.join(start + '\nOld shipped.\n' + end for start, end, _ in policies))
        with patch.object(installer, 'shipped_hashes', return_value={installer.digest('Old shipped.')}):
            self.assertEqual(installer.install(self.home, apply=True)['status'], 'updated')
        for start, end, body in policies:
            self.assertIn(start + '\n' + body + '\n' + end, self.target.read_text())

    def test_force_replaces_personal_block_and_backs_up(self):
        original = installer.OMH_START + '\nPersonal edit.\n' + installer.OMH_END
        self.seed(original)
        self.assertEqual(installer.install(self.home, force=True)['status'], 'update')
        self.assertFalse((self.home / '.agent-setup').exists())
        self.assertEqual(self.target.read_text(), original)
        self.assertEqual(installer.install(self.home, apply=True, force=True)['status'], 'updated')
        self.assertIn(installer.omh_policy(), self.target.read_text())
        backup = self.home / '.agent-setup/backups' / (installer.digest(original) + '.SOUL.md')
        self.assertEqual(backup.read_text(), original)

    def test_conflict_names_block_writes_diff_and_preserves_ledger(self):
        installer.install(self.home, apply=True)
        ledger = self.home / '.agent-setup/managed-blocks.json'
        before_ledger = ledger.read_bytes()
        self.target.write_text(self.target.read_text().replace(installer.delivery_policy(), 'Personal edit.'))
        before = self.target.read_bytes()
        with self.assertRaisesRegex(ValueError, 'document-delivery.*수동 편집.*차이 파일:'):
            installer.install(self.home, apply=True)
        self.assertEqual(self.target.read_bytes(), before)
        self.assertEqual(ledger.read_bytes(), before_ledger)
        diffs = list((self.home / '.agent-setup/diffs').glob('*.diff'))
        self.assertEqual(len(diffs), 1)
        self.assertIn('-Personal edit.', diffs[0].read_text())
        self.assertIn('+## Document delivery', diffs[0].read_text())

    def test_ledger_recognizes_previously_applied_uncommitted_template(self):
        with patch.object(installer, 'omh_policy', return_value='Previously applied template.'):
            installer.install(self.home, apply=True)
        ledger = self.home / '.agent-setup/managed-blocks.json'
        before = json.loads(ledger.read_text())
        self.assertIn(installer.digest('Previously applied template.'), before[installer.OMH_START])
        with patch.object(installer, 'shipped_hashes', return_value=set()):
            self.assertEqual(installer.install(self.home, apply=True)['status'], 'updated')
        after = json.loads(ledger.read_text())
        self.assertIn(installer.digest('Previously applied template.'), after[installer.OMH_START])
        self.assertIn(installer.digest(installer.omh_policy()), after[installer.OMH_START])
        self.assertEqual(len(after), 4)

    def test_late_conflict_preserves_earlier_pending_replacement(self):
        existing = (installer.COMMON_START + '\nOld shipped.\n' + installer.COMMON_END
                    + '\n' + installer.DELIVERY_START + '\nPersonal edit.\n' + installer.DELIVERY_END)
        self.seed(existing)
        with patch.object(installer, 'shipped_hashes', return_value={installer.digest('Old shipped.')}):
            with self.assertRaises(ValueError):
                installer.install(self.home, apply=True)
        self.assertEqual(self.target.read_text(), existing)
        self.assertFalse((self.home / '.agent-setup/managed-blocks.json').exists())

    def test_force_keeps_malformed_marker_refusal(self):
        self.seed(installer.OMH_END + '\nPersonal edit.\n' + installer.OMH_START)
        before = self.target.read_bytes()
        with self.assertRaisesRegex(ValueError, 'Malformed'):
            installer.install(self.home, apply=True, force=True)
        self.assertEqual(self.target.read_bytes(), before)

    def test_changed_omh_policy_preserves_whole_file(self):
        existing = (installer.OMH_START + '\n## OMH 워크플로 사용\nExisting rule.\n'
                    + installer.OMH_END + '\n')
        self.seed(existing)
        with self.assertRaisesRegex(ValueError, 'Existing managed'):
            installer.install(self.home, apply=True)
        self.assertEqual(self.target.read_text(), existing)

    def test_retired_managed_rule_is_not_validated_or_changed(self):
        existing = '<!-- hermes-setup:user-intent:begin -->\nPersonal edit.\n<!-- hermes-setup:user-intent:end -->\n'
        self.seed(existing)
        self.assertEqual(installer.install(self.home, apply=True)['status'], 'added')
        self.assertTrue(self.target.read_text().startswith(existing))
        self.assertEqual(self.target.read_text().count('hermes-setup:user-intent:begin'), 1)

    def test_delivery_policy_requires_folder_card_without_auto_open(self):
        body = installer.delivery_policy()
        self.assertIn('::preview{file=', body)
        self.assertIn('Do not automatically open Finder', body)
        self.assertIn('explicitly asks', body)

    def test_existing_unmarked_delivery_not_duplicated(self):
        existing = installer.delivery_policy() + '\n'
        self.seed(existing)
        installer.install(self.home, apply=True)
        updated = self.target.read_text()
        self.assertTrue(updated.startswith(existing))
        self.assertEqual(updated.count(installer.delivery_policy()), 1)
        self.assertNotIn(installer.DELIVERY_START, updated)

    def test_changed_delivery_rule_preserves_whole_file(self):
        existing = installer.DELIVERY_START + '\nPersonal edit.\n' + installer.DELIVERY_END + '\n'
        self.seed(existing)
        with self.assertRaises(ValueError):
            installer.install(self.home, apply=True)
        self.assertEqual(self.target.read_text(), existing)

    def test_retired_incomplete_rule_does_not_block_installation(self):
        self.seed('<!-- hermes-setup:user-intent:begin -->\nIncomplete.\n')
        before = self.target.read_bytes()
        self.assertEqual(installer.install(self.home, apply=True)['status'], 'added')
        self.assertTrue(self.target.read_bytes().startswith(before))

    def test_retired_template_is_not_an_installation_dependency(self):
        self.assertFalse((ROOT / 'templates/user-intent.md').exists())
        installer.install(self.home, apply=True)
        content = self.target.read_text()
        self.assertIn(installer.browser_policy(), content)
        self.assertIn(installer.delivery_policy(), content)
        self.assertNotIn('hermes-setup:user-intent:', content)

    def test_adds_browser_rule_to_existing_managed_report(self):
        report = installer.LEGACY_REPORT_START + '\nPersonal report policy.\n' + installer.LEGACY_REPORT_END + '\n'
        self.seed(report)
        self.assertEqual(installer.install(self.home, apply=True)['status'], 'added')
        updated = self.target.read_text()
        self.assertTrue(updated.startswith(report))
        self.assertEqual(updated.count(installer.BROWSER_START), 1)
        self.assertEqual(installer.install(self.home, apply=True)['status'], 'unchanged')
        self.assertEqual(installer.install(self.home)['legacy_report_policy'], 'present_preserved')

    def test_changed_browser_rule_is_conflict(self):
        existing = installer.BROWSER_START + '\nPersonal edit.\n' + installer.BROWSER_END + '\n'
        self.seed(existing)
        with self.assertRaises(ValueError):
            installer.install(self.home, apply=True)
        self.assertEqual(self.target.read_text(), existing)

    def test_preserves_existing_crlf_bytes(self):
        self.home.mkdir()
        existing = b'# My tone\r\nPersonal rules.\r\n'
        self.target.write_bytes(existing)
        installer.install(self.home, apply=True)
        self.assertTrue(self.target.read_bytes().startswith(existing))

    def test_personal_unmarked_report_policy_is_preserved(self):
        existing = '## Reports and AI-slop review\n\nMy existing policy.\n'
        self.seed(existing)
        result = installer.install(self.home, apply=True)
        self.assertEqual(result['status'], 'added')
        self.assertEqual(result['legacy_report_policy'], 'present_preserved')
        self.assertTrue(self.target.read_text().startswith(existing))

    def test_malformed_legacy_report_is_preserved(self):
        existing = installer.LEGACY_REPORT_START + '\nPersonal edit.\n'
        self.seed(existing)
        installer.install(self.home, apply=True)
        self.assertTrue(self.target.read_text().startswith(existing))

    def test_changed_managed_browser_block_is_conflict(self):
        self.seed(installer.BROWSER_START + '\nPersonal edit.\n' + installer.BROWSER_END + '\n')
        before = self.target.read_bytes()
        with self.assertRaises(ValueError):
            installer.install(self.home, apply=True)
        self.assertEqual(self.target.read_bytes(), before)

    def test_malformed_markers_are_conflict(self):
        self.seed(installer.BROWSER_START + '\nIncomplete.\n')
        with self.assertRaises(ValueError):
            installer.install(self.home, apply=True)

    def test_symlink_refused(self):
        self.home.mkdir()
        other = self.home / 'other.md'
        other.write_text('Keep me.')
        self.target.symlink_to(other)
        with self.assertRaises(ValueError):
            installer.install(self.home, apply=True)
        self.assertEqual(other.read_text(), 'Keep me.')

    def test_environment_home_and_explicit_home(self):
        with patch.dict(os.environ, {'HERMES_HOME': str(self.home)}):
            self.assertEqual(installer.resolve_home(), self.home)
            self.assertEqual(installer.resolve_home(str(self.home / 'other')), self.home / 'other')


if __name__ == '__main__':
    unittest.main()
