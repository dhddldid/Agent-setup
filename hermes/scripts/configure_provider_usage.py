#!/usr/bin/env python3
"""Restrict provider-usage desktop displays to GPT and Claude (preview by default)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

START = '// hermes-setup:gpt-claude-only:begin'
END = '// hermes-setup:gpt-claude-only:end'
BLOCK = """// hermes-setup:gpt-claude-only:begin
const SETUP_USAGE_PROVIDERS = Object.freeze(['openai-codex', 'anthropic'])
function setupUsageProviders(data) {
  const providers = data && Array.isArray(data.providers) ? data.providers : []
  return providers
    .filter(p => p && SETUP_USAGE_PROVIDERS.includes(p.id))
    .map(p => ({ ...p, name: p.id === 'openai-codex' ? 'GPT' : 'Claude' }))
}
// hermes-setup:gpt-claude-only:end"""
RULES = (
    ('const $barProviders = atom(null)', 'const $barProviders = atom([...SETUP_USAGE_PROVIDERS])'),
    ('if (Array.isArray(bar)) $barProviders.set(bar)',
     'if (Array.isArray(bar)) $barProviders.set([...bar])'),
    ('for (const p of data.providers)', 'for (const p of setupUsageProviders(data))'),
    ('const provs = data.providers || []', 'const provs = setupUsageProviders(data)'),
    ('const rows = data && Array.isArray(data.providers) ? data.providers : []',
     'const rows = setupUsageProviders(data)'),
    ('const provs = data && Array.isArray(data.providers) ? data.providers : []',
     'const provs = setupUsageProviders(data)'),
    ("'openai-codex': 'codex'", "'openai-codex': 'gpt'"),
)
# v0.4: the bar reads p.code from the payload, and staleBackend keeps reading
# every provider (it detects an old dashboard backend).
RULES_V04 = (
    RULES[0],
    RULES[1],
    ('    for (const p of data.providers) {', '    for (const p of setupUsageProviders(data)) {'),
    ('barModel(data.providers || [], barSet', 'barModel(setupUsageProviders(data), barSet'),
    RULES[4],
    RULES[5],
    ('code: p.code || p.id,', "code: p.id === 'openai-codex' ? 'gpt' : p.code || p.id,"),
)
# (anchor the block is inserted before, rules), oldest first; v0.2 sources also
# contain the v0.4 anchor, so the first profile that fits wins.
PROFILES = (('const WARN_PCT = 80', RULES), ('const INTERVALS = [', RULES_V04))


def fits(text, anchor, rules):
    return text.count(anchor) == 1 and all(text.count(old) == 1 and new not in text for old, new in rules)


def adapt(source):
    newline = '\r\n' if '\r\n' in source else '\n'
    text = source.replace('\r\n', '\n')
    if START in text or END in text:
        profile = next((rules for anchor, rules in PROFILES if BLOCK + '\n' + anchor in text), None)
        if text.count(START) != 1 or text.count(END) != 1 or profile is None:
            raise ValueError('Managed display filter differs; existing file preserved')
        remainder = text.replace(BLOCK + '\n', '', 1)
        # Upgrade only the complete, exact prior adapter. Validate all guards
        # against that version before changing its one storage-restore line.
        legacy_restore = 'if (Array.isArray(bar)) $barProviders.set(bar.filter(id => SETUP_USAGE_PROVIDERS.includes(id)))'
        restore = RULES[1][1]
        prior = legacy_restore in remainder
        rules = tuple((old, legacy_restore if new == restore and prior else new) for old, new in profile)
        for old, new in rules:
            expected = sum(replacement == new for original, replacement in rules)
            if remainder.count(new) != expected or old in remainder:
                raise ValueError('Partial or changed display filter; existing file preserved')
        if prior:
            if restore in remainder:
                raise ValueError('Mixed display filter versions; existing file preserved')
            return text.replace(legacy_restore, restore, 1).replace('\n', newline)
        return source
    if not any(text.count(anchor) == 1 for anchor, rules in PROFILES):
        raise ValueError('Unsupported plugin source; review the installed version')
    profile = next(((anchor, rules) for anchor, rules in PROFILES if fits(text, anchor, rules)), None)
    if profile is None:
        raise ValueError('Unsupported or customized display code; existing file preserved')
    anchor, rules = profile
    text = text.replace(anchor, BLOCK + '\n' + anchor, 1)
    for old, new in rules:
        text = text.replace(old, new, 1)
    return text.replace('\n', newline)


def safe_path(path):
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Refusing symlink path: ' + str(path))


def replace_bytes(target, content, mode):
    with tempfile.NamedTemporaryFile(dir=str(target.parent), prefix='.usage-', delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(content)
            stream.flush()
            os.fchmod(stream.fileno(), mode)
        except BaseException:
            temporary.unlink()
            raise
    try:
        os.replace(str(temporary), str(target))
    finally:
        if temporary.exists():
            temporary.unlink()


def install(home, apply=False, desktop_home=None):
    home = Path(home).expanduser().absolute()
    desktop = Path(desktop_home).expanduser().absolute() if desktop_home else home
    source = home / 'plugins/provider-usage/desktop/plugin.js'
    mirror = desktop / 'desktop-plugins/provider-usage/plugin.js'
    safe_path(source)
    if not source.is_file():
        raise FileNotFoundError('Install provider-usage before applying its display filter')
    safe_path(mirror)
    if desktop_home and not mirror.is_file():
        raise FileNotFoundError('Desktop plugin copy not found in the specified desktop home')
    targets = [source] + ([mirror] if mirror.is_file() and mirror != source else [])
    plans = []
    for target in targets:
        original = target.read_bytes()
        updated = adapt(original.decode('utf-8')).encode('utf-8')
        plans.append((target, original, updated, target.stat().st_mode & 0o777))
    # Check every target before changing either the source or its desktop copy.
    if apply:
        for target, original, updated, mode in plans:
            if target.read_bytes() != original:
                raise ValueError('Plugin changed during preflight; retry after reviewing it')
        for target, original, updated, mode in plans:
            if original == updated:
                continue
            backup = home / 'backups/provider-usage' / (hashlib.sha256(original).hexdigest() + '.js')
            safe_path(backup)
            backup.parent.mkdir(parents=True, exist_ok=True)
            if backup.exists():
                if backup.read_bytes() != original:
                    raise ValueError('Existing backup differs; file preserved')
            else:
                with open(os.open(str(backup), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as stream:
                    stream.write(original)
            safe_path(target)
            if target.read_bytes() != original:
                raise ValueError('Plugin changed before write; existing file preserved')
            replace_bytes(target, updated, mode)
    return {
        'apply': apply,
        'providers': ['openai-codex', 'anthropic'],
        'desktop_copy_present': mirror.is_file(),
        'files': [{'path': str(t), 'status': 'unchanged' if before == after else ('changed' if apply else 'change')}
                  for t, before, after, mode in plans],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', help='Selected Hermes home; defaults to HERMES_HOME or ~/.hermes')
    parser.add_argument('--desktop-home', help='Explicit desktop plugin home if different; app-level scope')
    parser.add_argument('--apply', action='store_true', help='Apply the display adapter after preflight')
    args = parser.parse_args()
    home = args.home or os.environ.get('HERMES_HOME') or str(Path.home() / '.hermes')
    print(json.dumps(install(home, args.apply, args.desktop_home), ensure_ascii=False))


if __name__ == '__main__':
    main()
