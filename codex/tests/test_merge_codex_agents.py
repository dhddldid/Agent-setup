import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import merge_codex_agents as m


class MergeCodexAgentsTests(unittest.TestCase):
    def run_merge(self, installed, templates, current):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            codex = root/'.codex'
            codex.mkdir()
            (codex/'AGENTS.md').write_text(installed)
            with patch.object(m, '_deployed_templates', return_value=iter(templates)), \
                 patch.object(m, '_render', side_effect=lambda text, home: text):
                status = m.merge(root, codex, root/'backups', template_text=current)
            return status, (codex/'AGENTS.md').read_text(), list((root/'backups').glob('*')) if (root/'backups').exists() else []

    def test_old_rendering_is_replaced_and_personal_tail_kept(self):
        status, text, backups = self.run_merge('OLD\n## personal\n- mine\n', ['OLD\n'], 'NEW\n')
        self.assertEqual(status, 'updated_personal_kept')
        self.assertEqual(text, 'NEW\n## personal\n- mine\n')
        self.assertEqual(len(backups), 1)

    def test_current_rendering_is_left_alone(self):
        status, text, backups = self.run_merge('NEW\n## personal\n', ['OLD\n'], 'NEW\n')
        self.assertEqual((status, text, backups), ('up_to_date', 'NEW\n## personal\n', []))

    def test_hand_edited_managed_part_is_not_touched(self):
        status, text, _ = self.run_merge('EDITED\n## personal\n', ['OLD\n'], 'NEW\n')
        self.assertEqual((status, text), ('user_modified', 'EDITED\n## personal\n'))

    def test_history_lookup_reads_real_git_log(self):
        templates = list(m._deployed_templates(limit=2))
        self.assertTrue(templates and all(isinstance(t, str) and t for t in templates))
        subprocess.run(['git', '-C', str(m.REPO), 'rev-parse', 'HEAD'], check=True, capture_output=True)


if __name__ == '__main__':
    unittest.main()
