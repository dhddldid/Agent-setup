#!/usr/bin/env python3
"""Check public documents, paths, links and the installation inventory."""
import json
from pathlib import Path
import re
import sys

# Support direct execution from the Hermes executor directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.latest_release import latest_release, tag_commit

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    skills = manifest['skills']
    assert len(skills) == 91 and len({s['name'] for s in skills}) == 91
    assert sum(s['source_kind'] == 'upstream' for s in skills) == 57
    assert sum(s['source_kind'] == 'local' for s in skills) == 34
    for s in skills:
        for key in ['source_path', 'install_path']:
            p = Path(s[key])
            assert not p.is_absolute() and '..' not in p.parts, (s['name'], key)
        if s['source_kind'] == 'local':
            assert (ROOT / s['source_path'] / 'SKILL.md').is_file()
    for record in [manifest['upstream'], *manifest['plugins'], manifest['omh']]:
        assert not {'commit', 'reference_commit', 'version'} & record.keys()
        repo = record['repo'].rstrip('/').removesuffix('.git').split('github.com/')[1]
        tag = latest_release(repo)
        assert tag, ('No stable release', repo)
        assert re.fullmatch(r'[0-9a-f]{40}', tag_commit(repo, tag))
    table = (ROOT / 'INSTALL-LIST.md').read_text()
    assert table.count('| 종류 |') == 1
    for s in skills:
        assert table.count('| ' + s['name'] + ' |') == 1, s['name']
    files = []
    for p in ROOT.rglob('*'):
        if not p.is_file() or any(x in p.relative_to(ROOT).parts for x in ['.git', '.local', '__pycache__']):
            continue
        assert not p.is_symlink(), p
        assert p.name not in ['.env', 'auth.json', 'state.db', 'USER.md'], p
        assert p.suffix not in ['.log', '.sqlite', '.db'], p
        files.append(p)
        if p.suffix not in ['.md', '.json', '.py', '.yml']:
            continue
        text = p.read_text()
        # Reject personal home paths and recognizable credential payloads.
        assert not re.search(r'/Users/[A-Za-z0-9_.-]+/', text), p
        assert not re.search(r'gh[pousr]_[A-Za-z0-9]{20,}|sk-ant-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{30,}', text), p
        if p.suffix == '.md':
            assert len(re.findall(r'^```', text, re.M)) % 2 == 0, p
            for target in re.findall(r'\]\(([^)]+)\)', text):
                if '://' in target or target.startswith('#'):
                    continue
                assert (p.parent / target.split('#')[0]).exists(), (p, target)
    print('PASS:', len(skills), 'skills; one installation table; public paths, links and credential-pattern checks;', len(files), 'files')


if __name__ == '__main__':
    main()
