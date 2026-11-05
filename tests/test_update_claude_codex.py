"""Updater contract and isolated, offline preview coverage."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/update_claude_codex.sh'


class UpdateClaudeCodexTests(unittest.TestCase):
    def test_static_contract(self):
        text = SCRIPT.read_text()
        self.assertIn('set -euo pipefail', text)
        self.assertNotRegex(text, r'v?\d+\.\d+\.\d+')
        self.assertNotRegex(text, r'\$[A-Za-z_][A-Za-z0-9_]*[^\x00-\x7F]')
        for required in ('latest_release', '--refresh', '--replace-existing',
                         'apply_skill_descriptions.py', 'install_core_skills', '--check'):
            self.assertIn(required, text)
        subprocess.run(['bash', '-n', str(SCRIPT)], check=True)

    def fixture(self, folder):
        repo = folder / 'repo'
        (repo / 'scripts').mkdir(parents=True)
        shutil.copy2(SCRIPT, repo / 'scripts/update_claude_codex.sh')
        (repo / 'scripts/latest_release.py').write_text(
            'def latest_release(repo): return "v9.8.7"\n')
        source = repo / 'shared/skills/omh/SOURCE.json'
        source.parent.mkdir(parents=True)
        source.write_text(json.dumps({'version': '0.0.1'}))
        home = folder / 'home'
        home.mkdir()
        env = dict(os.environ, HOME=str(home), PYTHON=sys.executable,
                   PYTHONDONTWRITEBYTECODE='1')
        env.pop('CLAUDE_CONFIG_DIR', None)
        env.pop('CODEX_HOME', None)
        return repo, home, env

    def test_empty_home_dry_run_and_check_are_read_only(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as directory:
            repo, home, env = self.fixture(Path(directory))
            before = {str(p.relative_to(repo)): p.read_bytes() for p in repo.rglob('*') if p.is_file()}
            for option in ('--dry-run', '--check'):
                done = subprocess.run(['bash', str(repo / 'scripts/update_claude_codex.sh'), option],
                                      env=env, capture_output=True, text=True)
                self.assertEqual(done.returncode, 0, done.stderr)
                self.assertIn('v9.8.7', done.stdout)
                self.assertIn('Claude Code 건너뜀', done.stdout)
                self.assertIn('Codex 건너뜀', done.stdout)
                self.assertIn('실행 전 | 실행 후', done.stdout)
                self.assertEqual(list(home.iterdir()), [])
            after = {str(p.relative_to(repo)): p.read_bytes() for p in repo.rglob('*') if p.is_file()}
            self.assertEqual(before, after)

    def test_present_executors_preview_commands_without_running_them(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as directory:
            repo, home, env = self.fixture(Path(directory))
            binaries = Path(directory) / 'bin'
            binaries.mkdir()
            for name in ('claude', 'codex'):
                executable = binaries / name
                executable.write_text('#!/bin/sh\nexit 99\n')
                executable.chmod(0o700)
                (home / ('.claude' if name == 'claude' else '.codex')).mkdir()
            env['PATH'] = str(binaries) + os.pathsep + env['PATH']
            done = subprocess.run(['bash', str(repo / 'scripts/update_claude_codex.sh'), '--dry-run'],
                                  env=env, capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertIn('claude/scripts/install.py', done.stdout)
            self.assertIn('install_core_skills', done.stdout)
            self.assertEqual(done.stdout.count('--replace-existing'), 2)
            self.assertFalse((home / '.agents').exists())

    def test_importer_accepts_release_tag_and_rejects_empty_source(self):
        spec = importlib.util.spec_from_file_location('import_omh_for_test', ROOT / 'scripts/import_omh_skills.py')
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as directory:
            folder = Path(directory)
            source, target = folder / 'source', folder / 'target'
            source.mkdir()
            with patch.object(module, 'TARGET', target), patch.object(module, 'ROOT', folder):
                with patch.object(sys, 'argv', ['import', '--source', str(source), '--version', 'v9.8.7']):
                    with self.assertRaises(SystemExit):
                        module.main()
                skill = source / 'guide/example'
                skill.mkdir(parents=True)
                (skill / 'SKILL.md').write_text('---\nname: example\ndescription: Example\n---\nBody\n')
                with patch.object(sys, 'argv', ['import', '--source', str(source), '--version', 'v9.8.7']):
                    module.main()
                self.assertEqual(json.loads((target / 'SOURCE.json').read_text())['version'], '9.8.7')


if __name__ == '__main__':
    unittest.main()
