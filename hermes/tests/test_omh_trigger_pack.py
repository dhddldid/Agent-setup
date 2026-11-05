"""Offline checks for the user trigger-pack installer."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/install_omh_trigger_pack.py'
SOURCE = Path(__file__).resolve().parents[1] / 'omh/trigger-packs/ko.json'


class TriggerPackTests(unittest.TestCase):
    def test_preview_apply_check_and_preserve_custom_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            target = home / 'routing/trigger-packs/ko.json'
            custom = {'schema_version': 'trigger_language_pack/v1', 'language': 'ko',
                      'skills': {'dag-ulw': ['내 프로젝트 작업을 분할해줘'],
                                 'code-review': ['사용자가 추가한 코드 검토']},
                      'whole_phrase_only_tokens': {'code-review': ['검토']}}
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps(custom, ensure_ascii=False), encoding='utf-8')
            original = target.read_bytes()
            def run(*args):
                return subprocess.run([sys.executable, str(SCRIPT), '--omh-home', str(home), *args],
                                      capture_output=True, text=True, check=False)
            preview = run()
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertIn('미리보기', preview.stdout)
            self.assertEqual(target.read_bytes(), original)
            self.assertEqual(run('--check').returncode, 1)
            applied = run('--apply')
            self.assertEqual(applied.returncode, 0, applied.stderr)
            merged = json.loads(target.read_text(encoding='utf-8'))
            self.assertEqual(merged['skills']['dag-ulw'][0], custom['skills']['dag-ulw'][0])
            self.assertEqual(merged['skills']['code-review'], custom['skills']['code-review'])
            self.assertEqual(merged['whole_phrase_only_tokens'], custom['whole_phrase_only_tokens'])
            self.assertEqual(run('--check').returncode, 0)
            stat = target.stat()
            self.assertEqual(run('--apply').returncode, 0)
            self.assertEqual(target.stat().st_mtime_ns, stat.st_mtime_ns)
            for skill, phrases in merged['skills'].items():
                self.assertEqual(len(phrases), len(set(phrases)), skill)

    def test_fresh_home_uses_environment_and_check_has_no_side_effects(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'routing/trigger-packs/ko.json'
            env = {**os.environ, 'OMH_HOME': directory}
            def run(*args):
                return subprocess.run([sys.executable, str(SCRIPT), *args], env=env,
                                      capture_output=True, text=True, check=False)
            self.assertEqual(run('--check').returncode, 1)
            self.assertFalse(target.parent.exists())
            self.assertEqual(run('--apply').returncode, 0)
            self.assertEqual(json.loads(target.read_text(encoding='utf-8')),
                             json.loads(SOURCE.read_text(encoding='utf-8')))
            self.assertEqual(run('--check').returncode, 0)

    def test_invalid_target_is_preserved(self):
        invalid = ['{', '[]', '{"language": "ko"}',
                   json.dumps({'schema_version': 'trigger_language_pack/v1', 'language': 'ko',
                               'skills': {'dag-ulw': ['same', 'same']}}),
                   json.dumps({'schema_version': 'trigger_language_pack/v1', 'language': 'ko',
                               'skills': {'dag-ulw': ['!!!']}})]
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'routing/trigger-packs/ko.json'
            target.parent.mkdir(parents=True)
            for text in invalid:
                with self.subTest(text=text):
                    target.write_text(text, encoding='utf-8')
                    result = subprocess.run([sys.executable, str(SCRIPT), '--omh-home', directory,
                                             '--apply'], capture_output=True, text=True, check=False)
                    self.assertEqual(result.returncode, 2, result.stdout)
                    self.assertIn('오류', result.stdout)
                    self.assertEqual(target.read_text(encoding='utf-8'), text)

    def test_source_holdbacks_merge_without_removing_custom_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            target = home / 'routing/trigger-packs/ko.json'
            target.parent.mkdir(parents=True)
            old = {'schema_version': 'trigger_language_pack/v1', 'language': 'ko',
                   'skills': {'dag-ulw': ['기존 작업 분할']},
                   'whole_phrase_only_tokens': {'dag-ulw': ['기존']}}
            new = {**old, 'skills': {'dag-ulw': ['기존 작업 분할', '새 작업 분할']},
                   'whole_phrase_only_tokens': {'dag-ulw': ['기존', '새작업']}}
            source = home / 'source.json'
            target.write_text(json.dumps(old), encoding='utf-8')
            source.write_text(json.dumps(new), encoding='utf-8')
            result = subprocess.run([sys.executable, str(SCRIPT), '--omh-home', directory,
                                     '--source', str(source), '--apply'], capture_output=True,
                                    text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(json.loads(target.read_text(encoding='utf-8')), new)

    def test_catalog_ids_and_task_specific_cues(self):
        source = json.loads(SOURCE.read_text(encoding='utf-8'))
        self.assertEqual(source['schema_version'], 'trigger_language_pack/v1')
        self.assertEqual(source['language'], 'ko')
        self.assertIn('dag-ulw', source['skills'])
        self.assertIn('ultrawork', source['skills'])
        self.assertNotIn('ulw-work', source['skills'])
        for skill, phrases in source['skills'].items():
            self.assertEqual(len(phrases), len(set(phrases)), skill)
            self.assertTrue(all(0 < len(phrase) <= 120 for phrase in phrases))
            self.assertTrue(all(len(phrase.split()) >= 2 for phrase in phrases))
            self.assertTrue({'병렬로', '끝까지', '해줘', '전부 반영해'}.isdisjoint(phrases))


if __name__ == '__main__':
    unittest.main()
