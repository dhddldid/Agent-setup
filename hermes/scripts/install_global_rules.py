#!/usr/bin/env python3
"""Install managed SOUL policies while preserving personal edits."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LEGACY_REPORT_START = '<!-- hermes-setup:report-writing:begin -->'
LEGACY_REPORT_END = '<!-- hermes-setup:report-writing:end -->'
LEGACY_REPORT_HEADING = '## Reports and AI-slop review'
BROWSER_START = '<!-- hermes-setup:aside-browser:begin -->'
BROWSER_END = '<!-- hermes-setup:aside-browser:end -->'
BROWSER_HEADING = '## Browser work in Aside'
DELIVERY_START = '<!-- hermes-setup:document-delivery:begin -->'
DELIVERY_END = '<!-- hermes-setup:document-delivery:end -->'
DELIVERY_HEADING = '## Document delivery in Hermes Desktop'
COMMON_START = '<!-- agent-setup:common:begin -->'
COMMON_END = '<!-- agent-setup:common:end -->'
COMMON_HEADING = '## 작업 원칙'
OMH_START = '<!-- agent-setup:omh-workflow:begin -->'
OMH_END = '<!-- agent-setup:omh-workflow:end -->'
OMH_HEADING = '## OMH workflow use'


def omh_policy():
    return (ROOT / 'templates/omh-workflow.md').read_text(encoding='utf-8').strip()


def browser_policy():
    return (ROOT / 'templates/aside-browser.md').read_text(encoding='utf-8').strip()


def common_policy():
    # Generated from Agent-setup shared/rules by scripts/build_rules.py.
    return (ROOT / 'templates/common-rules.md').read_text(encoding='utf-8').strip()


def delivery_policy():
    return (ROOT / 'templates/document-delivery.md').read_text(encoding='utf-8').strip()


def digest(body):
    return hashlib.sha256(body.encode('utf-8')).hexdigest()


def shipped_hashes(template):
    """Recognize all available committed template versions before ledger adoption."""
    relative = template.relative_to(ROOT.parent).as_posix()
    try:
        history = subprocess.run(
            ['git', 'log', '--format=%H', '--', relative], cwd=ROOT.parent,
            capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        return set()  # Archive installations rely on the apply ledger.
    if history.returncode:
        return set()
    hashes = set()
    for revision in history.stdout.splitlines():
        version = subprocess.run(
            ['git', 'show', f'{revision}:{relative}'], cwd=ROOT.parent,
            capture_output=True, check=False,
        )
        if version.returncode == 0:
            hashes.add(digest(version.stdout.decode('utf-8').strip()))
    return hashes


class PolicyConflict(ValueError):
    def __init__(self, name, current, proposed):
        self.name, self.current, self.proposed = name, current, proposed
        super().__init__(f'Existing managed {name}: 수동 편집 구간을 보존합니다')


def policy_status(existing, body, start_marker, end_marker, heading,
                  known_hashes=(), force=False):
    block = start_marker + '\n' + body + '\n' + end_marker
    if start_marker in existing or end_marker in existing:
        if existing.count(start_marker) != 1 or existing.count(end_marker) != 1:
            raise ValueError(f'Malformed or duplicated {heading} markers; existing file preserved')
        start = existing.index(start_marker)
        end_start = existing.index(end_marker)
        if end_start < start + len(start_marker):
            raise ValueError(f'Malformed {heading} marker order; existing file preserved')
        current = existing[start:end_start + len(end_marker)]
        if current == block:
            return 'unchanged', block
        # Exact framing preserves hand-edited whitespace as well as prose.
        inner = existing[start + len(start_marker):end_start]
        known = (inner.startswith('\n') and inner.endswith('\n')
                 and digest(inner[1:-1]) in known_hashes)
        if known or force:
            return 'update', block
        raise PolicyConflict(start_marker, current, block)
    if body in existing:
        return 'unchanged', block
    if heading in existing:
        raise ValueError(f'Existing {heading} policy differs; review it before changing; file preserved')
    return 'add', block


def resolve_home(explicit=None):
    value = explicit or os.environ.get('HERMES_HOME') or str(Path.home() / '.hermes')
    return Path(value).expanduser().absolute()


def install(home, apply=False, force=False):
    target = Path(home) / 'SOUL.md'
    if target.is_symlink():
        raise ValueError('Refusing SOUL.md symlink')
    state_dir = Path(home) / '.agent-setup'
    ledger_path = state_dir / 'managed-blocks.json'
    for path in (state_dir, ledger_path, state_dir / 'diffs', state_dir / 'backups'):
        if path.is_symlink():
            raise ValueError(f'Refusing managed state symlink: {path}')
    ledger = json.loads(ledger_path.read_text(encoding='utf-8')) if ledger_path.exists() else {}
    if not isinstance(ledger, dict) or any(
        not isinstance(values, list) or any(
            not isinstance(value, str) or len(value) != 64
            or any(c not in '0123456789abcdef' for c in value) for value in values
        ) for values in ledger.values()
    ):
        raise ValueError('Invalid managed-blocks.json; existing file preserved')
    existing = target.read_bytes().decode('utf-8') if target.exists() else ''
    policies = (
        (common_policy(), COMMON_START, COMMON_END, COMMON_HEADING, 'common-rules.md'),
        (omh_policy(), OMH_START, OMH_END, OMH_HEADING, 'omh-workflow.md'),
        (browser_policy(), BROWSER_START, BROWSER_END, BROWSER_HEADING, 'aside-browser.md'),
        (delivery_policy(), DELIVERY_START, DELIVERY_END, DELIVERY_HEADING, 'document-delivery.md'),
    )
    # Validate every policy against the original before touching SOUL or its ledger.
    additions, replacements = [], []
    for body, start, end, heading, template in policies:
        known = set(ledger.get(start, [])) | shipped_hashes(ROOT / 'templates' / template)
        try:
            policy_state, block = policy_status(existing, body, start, end, heading, known, force)
        except PolicyConflict as conflict:
            diff = ''.join(difflib.unified_diff(
                (conflict.current + '\n').splitlines(keepends=True),
                (conflict.proposed + '\n').splitlines(keepends=True),
                fromfile='SOUL.md:installed', tofile=f'templates/{template}',
            ))
            diff_path = state_dir / 'diffs' / (digest(diff) + '.diff')
            if apply:
                diff_path.parent.mkdir(parents=True, exist_ok=True)
                if diff_path.is_symlink():
                    raise ValueError('Refusing diff symlink')
                diff_path.write_text(diff, encoding='utf-8')
            note = '' if apply else ' (미리보기: --apply 실행 시 저장)'
            raise ValueError(f'{conflict}; 차이 파일: {diff_path}{note}; --force로 교체 가능') from None
        if policy_state == 'add':
            additions.append(block)
        elif policy_state == 'update':
            replacements.append((existing.index(start), existing.index(end) + len(end), block))
        ledger[start] = sorted(set(ledger.get(start, [])) | {digest(body)})
    status = 'update' if replacements else ('add' if additions else 'unchanged')
    updated = existing
    for left, right, block in sorted(replacements, reverse=True):
        updated = updated[:left] + block + updated[right:]
    if additions:
        separator = '' if not updated else ('\n' if updated.endswith('\n') else '\n\n')
        updated += separator + '\n\n'.join(additions) + '\n'
    legacy_report_present = any(token in existing for token in (
        LEGACY_REPORT_START, LEGACY_REPORT_END, LEGACY_REPORT_HEADING
    ))
    if apply:
        state_dir.mkdir(parents=True, exist_ok=True)
        if updated != existing:
            if target.exists():
                backup = state_dir / 'backups' / (digest(existing) + '.SOUL.md')
                backup.parent.mkdir(parents=True, exist_ok=True)
                if backup.is_symlink():
                    raise ValueError('Refusing backup symlink')
                backup.write_bytes(existing.encode('utf-8'))
            target.write_bytes(updated.encode('utf-8'))
            status = 'updated' if replacements else 'added'
        ledger_path.write_text(json.dumps(ledger, indent=2) + '\n', encoding='utf-8')
    return {
        'status': status, 'path': str(target), 'apply': apply,
        'legacy_report_policy': 'present_preserved' if legacy_report_present else 'absent',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', help='Chosen Hermes profile home; otherwise HERMES_HOME or ~/.hermes')
    parser.add_argument('--apply', action='store_true', help='Apply; default is read-only preview')
    parser.add_argument('--force', action='store_true', help='Replace hand-edited managed blocks')
    args = parser.parse_args()
    try:
        result = install(resolve_home(args.home), args.apply, args.force)
    except ValueError as error:
        parser.exit(1, str(error) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
