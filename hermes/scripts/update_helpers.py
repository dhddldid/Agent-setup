#!/usr/bin/env python3
"""Helpers for hermes/scripts/update.sh: version lookup, omh resolution, state snapshots.

Subcommands print shell assignments (for `eval`) or Korean report text:

  version-from-url URL              releases/latest redirect URL -> X.Y.Z
  hermes-info                       parse `hermes --version` on stdin
  omh-info [--bin PATH]             resolve the omh the user actually runs
  patch-exists --target T --tag T   does hermes/patches/<target>/<tag>.patch exist
  snapshot --out FILE ...           record customization state as JSON
  summary FILE                      Korean table of one snapshot
  diff BEFORE AFTER                 Korean kept/changed table
  legacy-check ...                  decide whether the legacy OMH venv can go
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STABLE_VERSION = re.compile(r'^\d+\.\d+\.\d+$')
CONFIG_KEYS = (
    'model', 'fallback_providers', 'delegation', 'skills.external_dirs', 'plugins.enabled',
    'memory.provider', 'agent.disabled_toolsets', 'mcp_servers.aside', 'updates',
)
OK_STATES = {'applied', 'unchanged', 'match'}
SOUL_MARKER = re.compile(r'<!-- ((?:agent|hermes)-setup:[a-z0-9-]+):begin -->\n(.*?)\n<!-- \1:end -->', re.S)


# ---------- pure logic (unit-tested) ----------

def version_from_redirect(url: str) -> str:
    """Return X.Y.Z from a GitHub .../releases/tag/vX.Y.Z redirect; reject anything else."""
    match = re.search(r'/releases/tag/v?([^/?#\s]+)\s*$', url.strip())
    if not match or not STABLE_VERSION.match(match.group(1)):
        raise ValueError(f'정식 릴리스 태그를 찾지 못했습니다: {url.strip() or "(빈 응답)"}')
    return match.group(1)


def parse_hermes_version(text: str) -> dict:
    version = re.search(r'Hermes Agent v(\d+\.\d+\.\d+)', text)
    channel = re.search(r'Hermes Agent v\S+(?: \([^)]*\))? · (\w+)', text)
    install = re.search(r'^Install directory:\s*(.+?)\s*$', text, re.M)
    return {'version': version.group(1) if version else '',
            'channel': channel.group(1) if channel else '',
            'install_dir': install.group(1) if install else ''}


def classify_direct_url(url: str) -> tuple[str, str]:
    """Map a pip direct_url to (channel, version) for OMH packages."""
    stable = re.search(r'/releases/download/v?(\d+\.\d+\.\d+)/', url)
    if stable:
        return 'stable', stable.group(1)
    if re.search(r'/archive/refs/heads/[^/]+\.zip$', url):
        return 'preview', ''
    if url.startswith('file:'):
        return 'local', ''
    return 'unknown', ''


def omh_layout(real: str) -> dict:
    """Locate the OMH root, generation and legacy venv from the real omh script path."""
    path = Path(real)
    parts = path.parts
    if len(parts) >= 5 and parts[-2:] == ('bin', 'omh') and parts[-3] == 'venv':
        if len(parts) >= 6 and parts[-5] == 'generations':
            root = Path(*parts[:-5])
            return {'kind': 'generation', 'root': str(root), 'generation': parts[-4]}
        root = Path(*parts[:-3])
        if (root / 'generations').is_dir():
            return {'kind': 'legacy', 'root': str(root), 'generation': ''}
    return {'kind': 'other', 'root': '', 'generation': ''}


def resolve_omh(bin_path: str) -> dict:
    real = os.path.realpath(bin_path)
    python = ''
    try:
        first = Path(real).read_bytes().split(b'\n', 1)[0].decode('utf-8', 'replace')
        if first.startswith('#!'):
            candidate = first[2:].strip().split()[0]
            if os.path.isabs(candidate) and os.access(candidate, os.X_OK):
                python = candidate
    except OSError:
        pass
    sibling = Path(real).parent / 'python'
    if not python and os.access(sibling, os.X_OK):
        python = str(sibling)
    return {'bin': bin_path, 'real': real, 'python': python, **omh_layout(real)}


def soul_blocks(text: str) -> dict:
    return {name: hashlib.sha256(body.encode('utf-8')).hexdigest() for name, body in SOUL_MARKER.findall(text)}


def override_chains(document: dict) -> dict:
    return {c['category']: c.get('chain_text', '') for c in document.get('categories', [])
            if c.get('origin') == 'override'}


def tree_hash(directory: Path) -> str:
    digest = hashlib.sha256()
    for file in sorted(p for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts):
        digest.update(file.relative_to(directory).as_posix().encode() + b'\0' + file.read_bytes() + b'\0')
    return digest.hexdigest()


def skill_inventory(skills_dir: Path) -> dict:
    """Hash user skills; skills listed in Hermes' .bundled_manifest are only counted."""
    manifest = skills_dir / '.bundled_manifest'
    bundled = set()
    if manifest.is_file():
        bundled = {line.split(':', 1)[0].strip() for line in manifest.read_text(encoding='utf-8').splitlines()
                   if line.strip()}
    custom, bundled_count = {}, 0
    if skills_dir.is_dir():
        for skill_md in sorted(skills_dir.rglob('SKILL.md')):
            relative = skill_md.parent.relative_to(skills_dir)
            if any(part.startswith('.') for part in relative.parts):
                continue
            name = skill_md.parent.name
            if name in bundled:
                bundled_count += 1
            else:
                custom[relative.as_posix()] = tree_hash(skill_md.parent)
    return {'custom': custom, 'bundled_count': bundled_count}


def snapshot_rows(snap: dict) -> dict:
    """Flatten a snapshot into {label: (kind, value)}; kind is 'value' or 'state'."""
    rows = {}
    chains = snap.get('model_chains') or {}
    for category, chain in sorted((chains.get('overrides') or {}).items()):
        rows[f'모델 체인 · {category}'] = ('value', chain)
    for key, value in (snap.get('config') or {}).items():
        rows[f'Hermes 설정 · {key}'] = ('value', None if value is None else json.dumps(value, sort_keys=True))
    for name, digest in sorted((snap.get('soul_blocks') or {}).items()):
        rows[f'SOUL 블록 · {name}'] = ('value', digest)
    if 'trigger_pack' in snap:
        rows['한국어 트리거 팩'] = ('value', snap['trigger_pack'])
    for name, state in (snap.get('states') or {}).items():
        rows[name] = ('state', state)
    return rows


def short(value) -> str:
    if value is None:
        return '없음'
    text = str(value)
    if re.fullmatch(r'[0-9a-f]{64}', text):
        return text[:10]
    return text if len(text) <= 60 else text[:57] + '...'


def diff_snapshots(before: dict, after: dict) -> list[dict]:
    """Compare two snapshots; each row has label, result, detail and attention."""
    rows = []
    old, new = snapshot_rows(before), snapshot_rows(after)
    for label in list(old) + [label for label in new if label not in old]:
        kind, previous = old[label] if label in old else (new[label][0], None)
        current = new.get(label, (kind, None))[1]
        if kind == 'state':
            ok = current in OK_STATES
            result = '적용됨' if ok else '확인 필요'
            rows.append({'label': label, 'result': result, 'detail': f'{short(previous)} → {short(current)}',
                         'attention': not ok})
            continue
        if previous == current:
            result, detail = '유지', short(current)
        elif previous is None:
            result, detail = '새로 생김', short(current)
        elif current is None:
            result, detail = '없어짐', short(previous)
        else:
            result, detail = '변경', f'{short(previous)} → {short(current)}'
        rows.append({'label': label, 'result': result, 'detail': detail, 'attention': result in ('없어짐', '변경')})
    skills_before = (before.get('skills') or {}).get('custom', {})
    skills_after = (after.get('skills') or {}).get('custom', {})
    missing = sorted(set(skills_before) - set(skills_after))
    changed = sorted(n for n in skills_before if n in skills_after and skills_before[n] != skills_after[n])
    added = sorted(set(skills_after) - set(skills_before))
    if missing or changed:
        detail = '; '.join(filter(None, [
            '없어짐 ' + ', '.join(missing) if missing else '',
            '변경 ' + ', '.join(changed) if changed else '']))
        rows.append({'label': f'사용자 스킬 ({len(skills_before)}개)', 'result': '변경',
                     'detail': detail, 'attention': True})
    else:
        extra = f', 새 스킬 {len(added)}개' if added else ''
        rows.append({'label': f'사용자 스킬 ({len(skills_before)}개)', 'result': '유지',
                     'detail': f'전부 그대로{extra}', 'attention': False})
    b_count = (before.get('skills') or {}).get('bundled_count', 0)
    a_count = (after.get('skills') or {}).get('bundled_count', 0)
    rows.append({'label': 'Hermes 기본 스킬', 'result': '유지' if b_count == a_count else '변경',
                 'detail': f'{b_count}개 → {a_count}개 (Hermes가 관리)', 'attention': False})
    return rows


def render_table(rows: list[dict]) -> str:
    lines = ['| 항목 | 결과 | 내용 |', '|---|---|---|']
    for row in rows:
        mark = '⚠ ' if row['attention'] else ''
        lines.append(f"| {row['label']} | {mark}{row['result']} | {row['detail']} |")
    attention = sum(row['attention'] for row in rows)
    lines.append('')
    lines.append(f'확인할 항목 {attention}건' if attention else '모든 사용자 지정이 그대로 유지되었습니다.')
    return '\n'.join(lines)


def legacy_verdict(facts: dict) -> tuple[bool, list[str]]:
    """Decide whether the legacy venv can be moved away, with Korean reasons."""
    reasons = []
    legacy = facts.get('legacy', '')
    if not facts.get('legacy_exists'):
        return False, [f'레거시 venv가 없습니다: {legacy}']
    if facts.get('legacy_is_symlink'):
        reasons.append('레거시 경로가 심볼릭 링크입니다')
    if facts.get('kind') != 'generation':
        reasons.append('PATH의 omh가 generation 설치본을 가리키지 않습니다')
    if facts.get('omh_real', '').startswith(legacy.rstrip('/') + '/'):
        reasons.append('PATH의 omh가 레거시 venv를 실행합니다')
    venv_dir = facts.get('omh_venv_dir_env', '')
    if venv_dir and not os.path.realpath(venv_dir).startswith(facts.get('root', '').rstrip('/') + '/'):
        reasons.append('OMH_VENV_DIR이 OMH 설치 루트 밖을 가리킵니다')
    for link in facts.get('path_links', []):
        reasons.append(f'PATH 명령이 레거시 venv를 가리킵니다: {link}')
    for process in facts.get('processes', []):
        reasons.append(f'레거시 venv를 쓰는 프로세스가 있습니다: {process}')
    expected = facts.get('expected_version', '')
    if expected and (facts.get('installed') != expected or facts.get('channel') != 'stable'):
        reasons.append(f"현재 omh가 정식 {expected}이 아닙니다 ({facts.get('channel')} {facts.get('installed')})")
    return not reasons, reasons


# ---------- environment probes ----------

def run(command, **kwargs):
    try:
        return subprocess.run(command, capture_output=True, text=True, check=False, **kwargs)
    except OSError as error:
        return subprocess.CompletedProcess(command, 127, '', str(error))


def omh_package(python: str) -> tuple[str, str]:
    if not python:
        return '', ''
    code = ('import importlib.metadata as m; d=m.distribution("oh-my-hermes"); '
            'print(d.version); print(d.read_text("direct_url.json") or "{}")')
    result = run([python, '-I', '-c', code])
    if result.returncode:
        return '', ''
    version, _, raw = result.stdout.partition('\n')
    try:
        url = json.loads(raw or '{}').get('url', '')
    except json.JSONDecodeError:
        url = ''
    return version.strip(), url


def state_of(command, key, cwd=None):
    result = run(command, cwd=cwd)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return 'error' if result.returncode else 'unknown'
    return key(payload)


def take_snapshot(args) -> dict:
    py, scripts = sys.executable, ROOT / 'scripts'
    hermes_home, omh_home = Path(args.hermes_home), Path(args.omh_home)
    snap: dict[str, Any] = {'config': {}, 'states': {}}
    chains = run([args.omh_bin, 'model-chains', 'show', '--json'])
    try:
        snap['model_chains'] = {'overrides': override_chains(json.loads(chains.stdout))}
    except json.JSONDecodeError:
        snap['model_chains'] = {'overrides': {}, 'error': (chains.stderr or chains.stdout)[-300:]}
    for key in CONFIG_KEYS:
        result = run(['hermes', 'config', 'get', '--json', key])
        try:
            snap['config'][key] = json.loads(result.stdout) if result.returncode == 0 else None
        except json.JSONDecodeError:
            snap['config'][key] = None
    soul = hermes_home / 'SOUL.md'
    snap['soul_blocks'] = soul_blocks(soul.read_text(encoding='utf-8')) if soul.is_file() else {}
    snap['skills'] = skill_inventory(hermes_home / 'skills')
    pack = omh_home / 'routing/trigger-packs/ko.json'
    snap['trigger_pack'] = hashlib.sha256(pack.read_bytes()).hexdigest() if pack.is_file() else None
    states = snap['states']
    patches = run([py, str(scripts / 'apply_local_patches.py'), '--home', str(hermes_home)])
    try:
        for row in json.loads(patches.stdout):
            states[f"로컬 패치 · {row['target']}"] = row['status']
    except (json.JSONDecodeError, KeyError, TypeError):
        states['로컬 패치'] = 'error'
    for name, script in (('위임 effort 보존', 'configure_delegation_reasoning.py'),
                         ('GPT 자식 fallback 순서', 'configure_gpt_fallback.py')):
        states[f'호환 패치 · {name}'] = state_of(
            [py, str(scripts / script), '--source-root', args.hermes_checkout], lambda p: p.get('status', 'unknown'))
    states['provider-usage 표시'] = state_of(
        [py, str(scripts / 'configure_provider_usage.py'), '--home', str(hermes_home)],
        lambda p: 'unchanged' if all(f['status'] == 'unchanged' for f in p.get('files', [])) else 'change')
    rules = run([py, str(scripts / 'install_global_rules.py'), '--home', str(hermes_home)])
    try:
        states['SOUL 설치기'] = json.loads(rules.stdout)['status']
    except (json.JSONDecodeError, KeyError):
        states['SOUL 설치기'] = 'conflict' if rules.returncode else 'unknown'
        snap['soul_installer_message'] = (rules.stderr or rules.stdout).strip()[-400:]
    pack_check = run([py, str(scripts / 'install_omh_trigger_pack.py'), '--omh-home', str(omh_home), '--check'])
    states['한국어 트리거 팩 설치'] = {0: 'match', 1: 'missing'}.get(pack_check.returncode, 'invalid')
    return snap


def legacy_facts(args) -> dict:
    info = resolve_omh(args.omh_bin)
    root = info['root']
    legacy = os.environ.get('OMH_VENV_DIR') or (os.path.join(root, 'venv') if root else '')
    installed, url = omh_package(info['python'])
    channel, _ = classify_direct_url(url)
    links = []
    prefix = os.path.realpath(legacy).rstrip('/') + '/' if legacy else None
    for directory in dict.fromkeys(os.environ.get('PATH', '').split(os.pathsep)):
        if not prefix or not os.path.isdir(directory):
            continue
        try:
            entries = os.scandir(directory)
        except OSError:
            continue
        with entries:
            for entry in entries:
                if entry.is_symlink() and os.path.realpath(entry.path).startswith(prefix):
                    links.append(entry.path)
    processes = []
    if prefix:
        ps = run(['ps', '-axo', 'pid=,command='])
        processes = [line.strip()[:120] for line in ps.stdout.splitlines()
                     if prefix + 'bin/' in line or (legacy.rstrip('/') + '/bin/') in line]
    return {'legacy': legacy, 'legacy_exists': bool(legacy) and os.path.isdir(legacy),
            'legacy_is_symlink': bool(legacy) and os.path.islink(legacy), 'kind': info['kind'],
            'root': root, 'omh_real': info['real'], 'omh_venv_dir_env': os.environ.get('OMH_VENV_DIR', ''),
            'path_links': links, 'processes': processes, 'expected_version': args.expected_version,
            'installed': installed, 'channel': channel}


# ---------- CLI ----------

def assignments(values: dict) -> str:
    return '\n'.join(f'{name}={shlex.quote(str(value))}' for name, value in values.items())


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('version-from-url')
    p.add_argument('url')
    sub.add_parser('hermes-info')
    p = sub.add_parser('omh-info')
    p.add_argument('--bin', default='')
    p = sub.add_parser('patch-exists')
    p.add_argument('--target', required=True)
    p.add_argument('--tag', required=True)
    p = sub.add_parser('snapshot')
    for name in ('--out', '--hermes-home', '--omh-home', '--hermes-checkout', '--omh-bin'):
        p.add_argument(name, required=True)
    p = sub.add_parser('summary')
    p.add_argument('file')
    p = sub.add_parser('diff')
    p.add_argument('before')
    p.add_argument('after')
    p = sub.add_parser('legacy-check')
    p.add_argument('--omh-bin', required=True)
    p.add_argument('--expected-version', default='')
    args = parser.parse_args(argv)

    if args.command == 'version-from-url':
        try:
            print(version_from_redirect(args.url))
        except ValueError as error:
            print(error, file=sys.stderr)
            return 2
    elif args.command == 'hermes-info':
        info = parse_hermes_version(sys.stdin.read())
        print(assignments({'HERMES_INSTALLED': info['version'], 'HERMES_CHANNEL': info['channel'],
                           'HERMES_CHECKOUT': info['install_dir']}))
    elif args.command == 'omh-info':
        binary = args.bin or next((os.path.join(d, 'omh') for d in os.environ.get('PATH', '').split(os.pathsep)
                                   if os.access(os.path.join(d, 'omh'), os.X_OK)), '')
        if not binary:
            print('PATH에서 omh를 찾지 못했습니다', file=sys.stderr)
            return 2
        info = resolve_omh(binary)
        installed, url = omh_package(info['python'])
        channel, _ = classify_direct_url(url)
        print(assignments({'OMH_BIN': info['bin'], 'OMH_REAL': info['real'], 'OMH_PY': info['python'],
                           'OMH_KIND': info['kind'], 'OMH_ROOT': info['root'], 'OMH_GENERATION': info['generation'],
                           'OMH_INSTALLED': installed, 'OMH_CHANNEL': channel, 'OMH_SOURCE_URL': url}))
    elif args.command == 'patch-exists':
        return 0 if (ROOT / 'patches' / args.target / f'{args.tag}.patch').is_file() else 1
    elif args.command == 'snapshot':
        snap = take_snapshot(args)
        Path(args.out).write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding='utf-8')
    elif args.command == 'summary':
        snap = json.loads(Path(args.file).read_text(encoding='utf-8'))
        lines = ['| 항목 | 현재 |', '|---|---|']
        lines += [f'| {label} | {short(value)} |' for label, (_, value) in snapshot_rows(snap).items()]
        skills = snap.get('skills', {})
        lines.append(f"| 사용자 스킬 | {len(skills.get('custom', {}))}개 (Hermes 기본 {skills.get('bundled_count', 0)}개 별도) |")
        if snap.get('soul_installer_message'):
            lines.append(f"\nSOUL 설치기: {snap['soul_installer_message']}")
        print('\n'.join(lines))
    elif args.command == 'diff':
        before = json.loads(Path(args.before).read_text(encoding='utf-8'))
        after = json.loads(Path(args.after).read_text(encoding='utf-8'))
        rows = diff_snapshots(before, after)
        print(render_table(rows))
    elif args.command == 'legacy-check':
        facts = legacy_facts(args)
        safe, reasons = legacy_verdict(facts)
        print(assignments({'LEGACY_VENV': facts['legacy'], 'LEGACY_SAFE': int(safe),
                           'LEGACY_REASONS': '; '.join(reasons)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
