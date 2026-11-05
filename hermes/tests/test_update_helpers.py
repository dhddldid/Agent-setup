"""Offline checks for update.sh helper logic (no network, temporary homes only)."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import update_helpers as h  # noqa: E402

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/update_helpers.py'


def snapshot(**overrides):
    base = {
        'model_chains': {'overrides': {'deep': 'claude-opus-5-5:high, gpt-6.1-sol:high'}},
        'config': {'fallback_providers': [{'provider': 'openai-codex', 'model': 'gpt-6.1-sol'}]},
        'soul_blocks': {'agent-setup:common': 'a' * 64},
        'skills': {'custom': {'research/mine': '1' * 64}, 'bundled_count': 58},
        'trigger_pack': 'b' * 64,
        'states': {'로컬 패치 · hermes-agent': 'no_patch'},
    }
    base.update(overrides)
    return base


class VersionTests(unittest.TestCase):
    def test_redirect_to_stable_version(self):
        self.assertEqual(h.version_from_redirect('https://github.com/rlaope/oh-my-hermes/releases/tag/v4.0.6\n'),
                         '4.0.6')
        self.assertEqual(h.version_from_redirect('https://github.com/x/y/releases/tag/0.22.7'), '0.22.7')

    def test_redirect_rejects_non_release_targets(self):
        for url in ('', 'https://github.com/x/y/releases', 'https://github.com/x/y/releases/tag/v5.0.0-rc1'):
            with self.assertRaises(ValueError):
                h.version_from_redirect(url)
        result = subprocess.run([sys.executable, str(SCRIPT), 'version-from-url', 'https://x/releases'],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn('정식 릴리스', result.stderr)

    def test_hermes_version_output(self):
        text = ('Hermes Agent v0.22.5 (2026.9.24) · stable · local bf0203a794a0\n'
                'Install directory: /opt/hermes/hermes-agent\nInstall method: git\n')
        self.assertEqual(h.parse_hermes_version(text),
                         {'version': '0.22.5', 'channel': 'stable', 'install_dir': '/opt/hermes/hermes-agent'})

    def test_direct_url_channel(self):
        self.assertEqual(h.classify_direct_url(
            'https://github.com/rlaope/oh-my-hermes/releases/download/v4.0.5/oh_my_hermes-4.0.5-py3-none-any.whl'),
            ('stable', '4.0.5'))
        self.assertEqual(h.classify_direct_url('https://github.com/rlaope/oh-my-hermes/archive/refs/heads/main.zip'),
                         ('preview', ''))
        self.assertEqual(h.classify_direct_url('file:///src/omh'), ('local', ''))


class OmhResolutionTests(unittest.TestCase):
    def test_follows_path_link_through_current_to_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            root = base / 'share/omh'
            venv_bin = root / 'generations/20261104-abc/venv/bin'
            venv_bin.mkdir(parents=True)
            python = venv_bin / 'python'
            python.symlink_to(sys.executable)
            (venv_bin / 'omh').write_text(f'#!{python}\nimport omh\n')
            (root / 'current').symlink_to('generations/20261104-abc')
            (root / 'venv/bin').mkdir(parents=True)
            (base / 'bin').mkdir()
            (base / 'bin/omh').symlink_to(root / 'current/venv/bin/omh')
            info = h.resolve_omh(str(base / 'bin/omh'))
            self.assertEqual(info['real'], str(venv_bin / 'omh'))
            self.assertEqual(info['python'], str(python))
            self.assertEqual((info['kind'], info['root'], info['generation']),
                             ('generation', str(root), '20261104-abc'))
            legacy = h.omh_layout(str(root / 'venv/bin/omh'))
            self.assertEqual((legacy['kind'], legacy['root']), ('legacy', str(root)))
            self.assertEqual(h.omh_layout('/usr/local/bin/omh')['kind'], 'other')

    def test_legacy_verdict(self):
        facts = {'legacy': '/r/venv', 'legacy_exists': True, 'legacy_is_symlink': False, 'kind': 'generation',
                 'root': '/r', 'omh_real': '/r/generations/g/venv/bin/omh', 'omh_venv_dir_env': '',
                 'path_links': [], 'processes': [], 'expected_version': '4.0.6', 'installed': '4.0.6',
                 'channel': 'stable'}
        self.assertEqual(h.legacy_verdict(facts), (True, []))
        safe, reasons = h.legacy_verdict({**facts, 'channel': 'preview', 'installed': '4.0.5',
                                          'path_links': ['/bin/omh-old'], 'omh_venv_dir_env': '/elsewhere/venv'})
        self.assertFalse(safe)
        self.assertEqual(len(reasons), 3)
        self.assertFalse(h.legacy_verdict({**facts, 'legacy_exists': False})[0])


class SnapshotTests(unittest.TestCase):
    def test_soul_blocks_and_overrides(self):
        text = ('intro\n<!-- agent-setup:common:begin -->\nrule\n<!-- agent-setup:common:end -->\n'
                '<!-- hermes-setup:aside-browser:begin -->\nbrowser\n<!-- hermes-setup:aside-browser:end -->\n')
        blocks = h.soul_blocks(text)
        self.assertEqual(sorted(blocks), ['agent-setup:common', 'hermes-setup:aside-browser'])
        self.assertNotEqual(blocks['agent-setup:common'], blocks['hermes-setup:aside-browser'])
        doc = {'categories': [{'category': 'deep', 'chain_text': 'a:high', 'origin': 'override'},
                              {'category': 'quick', 'chain_text': 'b:low', 'origin': 'default'}]}
        self.assertEqual(h.override_chains(doc), {'deep': 'a:high'})

    def test_skill_inventory_separates_bundled(self):
        with tempfile.TemporaryDirectory() as directory:
            skills = Path(directory)
            for relative in ('apple/apple-notes', 'research/mine', '.hub/cached'):
                (skills / relative).mkdir(parents=True)
                (skills / relative / 'SKILL.md').write_text(relative)
            (skills / '.bundled_manifest').write_text('apple-notes:abc\n')
            inventory = h.skill_inventory(skills)
            self.assertEqual(inventory['bundled_count'], 1)
            self.assertEqual(list(inventory['custom']), ['research/mine'])

    def test_diff_reports_kept_changed_and_lost(self):
        before = snapshot()
        same = h.diff_snapshots(before, json.loads(json.dumps(before)))
        self.assertTrue(all(r['result'] in ('유지', '확인 필요') for r in same))
        after = snapshot(model_chains={'overrides': {}},
                         skills={'custom': {'research/mine': '2' * 64}, 'bundled_count': 60},
                         states={'로컬 패치 · hermes-agent': 'applied'},
                         soul_blocks={'agent-setup:common': 'a' * 64, 'agent-setup:omh-workflow': 'c' * 64})
        rows = {r['label']: r for r in h.diff_snapshots(before, after)}
        self.assertEqual(rows['모델 체인 · deep']['result'], '없어짐')
        self.assertEqual(rows['로컬 패치 · hermes-agent']['result'], '적용됨')
        self.assertEqual(rows['SOUL 블록 · agent-setup:omh-workflow']['result'], '새로 생김')
        self.assertEqual(rows['사용자 스킬 (1개)']['result'], '변경')
        self.assertIn('research/mine', rows['사용자 스킬 (1개)']['detail'])
        self.assertFalse(rows['Hermes 기본 스킬']['attention'])
        table = h.render_table(list(rows.values()))
        self.assertIn('| 항목 | 결과 | 내용 |', table)
        self.assertIn('확인할 항목 2건', table)

    def test_diff_cli_prints_korean_table(self):
        with tempfile.TemporaryDirectory() as directory:
            before, after = Path(directory, 'before.json'), Path(directory, 'after.json')
            before.write_text(json.dumps(snapshot()), encoding='utf-8')
            after.write_text(json.dumps(snapshot(states={'로컬 패치 · hermes-agent': 'applied'})), encoding='utf-8')
            result = subprocess.run([sys.executable, str(SCRIPT), 'diff', str(before), str(after)],
                                    capture_output=True, text=True, check=False, env={**os.environ})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('모든 사용자 지정이 그대로 유지되었습니다.', result.stdout)
            self.assertIn('no_patch → applied', result.stdout)


class UpdateScriptTextTests(unittest.TestCase):
    def test_variables_before_non_ascii_text_use_braces(self):
        # Under `set -u`, bash reads a multibyte letter right after `$NAME` as part of the name.
        import re
        script = (Path(__file__).resolve().parents[1] / 'scripts' / 'update.sh').read_text(encoding='utf-8')
        bad = [n for n, line in enumerate(script.splitlines(), 1)
               if re.search(r'\$[A-Za-z_][A-Za-z0-9_]*[^\x00-\x7F]', line)]
        self.assertEqual(bad, [], f'use ${{NAME}} before non-ASCII text on lines {bad}')


if __name__ == '__main__':
    unittest.main()
