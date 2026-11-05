#!/usr/bin/env bash
# Refresh the release copy and installed executor rules/skills from this checkout.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE=apply
case "${1:-}" in
  '') ;;
  --dry-run) MODE=dry-run ;;
  --check) MODE=check ;;
  --help|-h) printf '사용법: bash scripts/update_claude_codex.sh [--dry-run|--check]\n'; exit 0 ;;
  *) printf '알 수 없는 옵션: %s\n' "$1" >&2; exit 2 ;;
esac
if [[ $# -gt 1 ]]; then printf '옵션은 하나만 지정하세요.\n' >&2; exit 2; fi
PYTHON="${PYTHON:-}"
if [[ -z "${PYTHON}" ]]; then
  for candidate in python3.14 python3.13 python3.12 python3; do
    if command -v "${candidate}" >/dev/null 2>&1 && "${candidate}" -c 'import sys; sys.exit(sys.version_info < (3,12))'; then
      PYTHON="${candidate}"; break
    fi
  done
fi
if [[ -z "${PYTHON}" ]]; then printf 'Python 3.12 이상이 필요합니다.\n' >&2; exit 1; fi
export PYTHONDONTWRITEBYTECODE=1
"${PYTHON}" - "${ROOT}" "${MODE}" <<'PY'
import datetime
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request

root, mode = Path(sys.argv[1]), sys.argv[2]
sys.path.insert(0, str(root))
from scripts.latest_release import latest_release

home = Path.home()
claude_home = Path(os.environ.get('CLAUDE_CONFIG_DIR') or home / '.claude').expanduser()
codex_home = Path(os.environ.get('CODEX_HOME') or home / '.codex').expanduser()
executors = [('Claude Code', 'claude', claude_home, claude_home / 'skills'),
             ('Codex', 'codex', codex_home, home / '.agents/skills')]
active = [row for row in executors if shutil.which(row[1]) and row[2].is_dir()]
source_file = root / 'shared/skills/omh/SOURCE.json'

def snapshot():
    version = json.loads(source_file.read_text())['version']
    values = {'OMH 사본 버전': version}
    for label, _, config, skills in executors:
        values[label + ' 스킬 수'] = str(sum(1 for p in skills.glob('*/SKILL.md') if p.is_file()))
        rules = config / 'AGENTS.md'
        values[label + ' 규칙 SHA256'] = hashlib.sha256(rules.read_bytes()).hexdigest() if rules.is_file() else '없음'
    return values

def run(*args):
    command = [sys.executable, *map(str, args)]
    print('실행: ' + shlex.join(command), flush=True)
    if mode == 'apply':
        subprocess.run(command, cwd=root, check=True)

ASIDE_STUB = 'This file is only an entry point'

def restore_aside_stub(skills):
    # Aside CLI updates replace aside-browser with its own entry stub; put the shared skill back.
    target = skills / 'aside-browser'
    skill = target / 'SKILL.md'
    if not skill.is_file() or ASIDE_STUB not in skill.read_text(errors='replace'):
        return
    print('Aside 진입점 스텁을 공통 aside-browser 스킬로 되돌립니다: ' + str(target), flush=True)
    if mode == 'apply':
        backup = home / 'Downloads/Codex-Setup-Backups' / ('aside-stub-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S')) / skills.parent.name
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(target, backup)
        shutil.rmtree(target)
        shutil.copytree(root / 'shared/skills/core/aside-browser', target)

before = snapshot()
tag = latest_release('rlaope/oh-my-hermes')
if not tag:
    raise SystemExit('OMH 최신 정식 릴리스를 찾을 수 없습니다.')
print('OMH 최신 정식 릴리스: ' + tag, flush=True)
for label, cli, config, _ in executors:
    if not any(row[0] == label for row in active):
        print(f'{label} 건너뜀: CLI 또는 홈 경로 확인 필요 ({config})', flush=True)

if mode != 'check':
    if before['OMH 사본 버전'].removeprefix('v') != tag.removeprefix('v'):
        print(f'OMH 공식 소스 사본 갱신: {before["OMH 사본 버전"]} → {tag}', flush=True)
        if mode == 'apply':
            # Use the official release archive, never an installed or mutable branch tree.
            scratch = Path(os.environ.get('TMPDIR') or home / '.cache/agent-setup')
            scratch.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='omh-release-', dir=scratch) as folder:
                folder = Path(folder)
                archive = folder / 'source.tar.gz'
                url = 'https://codeload.github.com/rlaope/oh-my-hermes/tar.gz/refs/tags/' + urllib.parse.quote(tag, safe='')
                with urllib.request.urlopen(url, timeout=60) as response, archive.open('wb') as output:
                    shutil.copyfileobj(response, output)
                with tarfile.open(archive) as bundle:
                    bundle.extractall(folder / 'source', filter='data')
                sources = list((folder / 'source').glob('*/skills'))
                if len(sources) != 1:
                    raise RuntimeError('OMH 공식 소스의 skills 경로를 확인하세요.')
                run(root / 'scripts/import_omh_skills.py', '--source', sources[0], '--version', tag)
    for label, cli, config, skills in active:
        restore_aside_stub(skills)
        if cli == 'claude':
            preset_file = config / 'agent-setup/routing.json'
            preset = json.loads(preset_file.read_text())['preset'] if preset_file.is_file() else 'claude-generous'
            run(root / 'claude/scripts/install.py', '--home', config, '--preset', preset, '--apply')
        else:
            # AGENTS.md keeps a personal tail, so apply_managed preserves it; merge_codex_agents
            # refreshes only the managed prefix. Any other preserved file stops the update.
            code = ('import sys; from pathlib import Path; '
                    'sys.path.insert(0, sys.argv[1]); from apply_managed import apply; '
                    'r=apply(Path(sys.argv[2]),Path(sys.argv[2])/"Downloads/Codex-Setup-Backups",True,codex_home=Path(sys.argv[3])); '
                    'print(r); other=[p for p in r["preserved"] if Path(p).name != "AGENTS.md"]; '
                    'sys.exit(1 if other else 0)')
            run('-c', code, root / 'codex/scripts', home, config)
            if mode != 'dry-run':
                run(root / 'codex/scripts/merge_codex_agents.py', home, config)
            code = ('import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); '
                    'from install_core_skills import install; r=install(home=Path(sys.argv[2])); print(r); '
                    'sys.exit(1 if any("preserved" in v for v in r.values()) else 0)')
            run('-c', code, root / 'codex/scripts', home)
        run(root / 'codex/scripts/install_external_skills.py', '--all', '--apply', '--refresh',
            '--replace-existing', '--home', home, '--skills-dir', skills)
        run(root / 'codex/scripts/apply_skill_descriptions.py', '--skill-root', skills, '--apply')

after = snapshot()
print('\n항목 | 실행 전 | 실행 후')
print('--- | --- | ---')
for name, value in before.items():
    print(f'{name} | {value} | {after[name]}')
if mode == 'dry-run':
    print('미리보기 완료: 원본과 설치 홈을 유지했습니다.')
elif mode == 'check':
    print('점검 완료: 최신 릴리스와 현재 설치 상태를 표시했습니다.')
else:
    print('업데이트 완료: 새 세션에서 규칙과 스킬을 확인하세요.')
PY
