"""Refresh the managed part of ~/.codex/AGENTS.md and keep the personal tail.

~/.codex/AGENTS.md is the rendered template followed by machine-specific personal
sections. apply_managed preserves the whole file once anything was appended, so the
updater calls this module: it finds which earlier template rendering the installed
file starts with (git history of codex/instructions/AGENTS.md), replaces only that
prefix with the current rendering, and backs the old file up first. A file whose
start matches no deployed rendering was edited by hand and is left untouched.
"""
import datetime
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import apply_managed as am  # noqa: E402

ROOT = am.ROOT
TEMPLATE = 'codex/instructions/AGENTS.md'
REPO = ROOT.parent


def _render(text, home):
    return am.render_text(text.replace('{{SETUP_ROOT}}', str(ROOT)), home)


def _deployed_templates(limit=50):
    commits = subprocess.check_output(['git', '-C', str(REPO), 'log', f'-{limit}', '--format=%H', '--', TEMPLATE],
                                      text=True).split()
    for commit in commits:
        yield subprocess.check_output(['git', '-C', str(REPO), 'show', f'{commit}:{TEMPLATE}'], text=True)


def merge(home, codex_home, backups, template_text=None):
    target = codex_home / 'AGENTS.md'
    if not target.is_file():
        return 'missing'
    installed = target.read_text()
    current = _render(template_text if template_text is not None else (REPO / TEMPLATE).read_text(), home)
    if installed.startswith(current):
        return 'up_to_date'
    for template in _deployed_templates():
        previous = _render(template, home)
        if installed.startswith(previous):
            backups.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backups / f'AGENTS.md.{datetime.datetime.now():%Y%m%d-%H%M%S}')
            target.write_text(current + installed[len(previous):])
            return 'updated_personal_kept'
    return 'user_modified'


if __name__ == '__main__':
    home, codex_home = Path(sys.argv[1]), Path(sys.argv[2])
    status = merge(home, codex_home, home / 'Library/Application Support/codex-setup/managed-backups')
    print({'codex_agents_md': status})
    sys.exit(1 if status == 'user_modified' else 0)
