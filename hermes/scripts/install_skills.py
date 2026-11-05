#!/usr/bin/env python3
"""Install the listed skill folders without overwriting existing skills."""
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys

# Support direct execution from the Hermes executor directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.latest_release import latest_release, tag_commit

ROOT = Path(__file__).resolve().parents[1]


def within(base, relative):
    parts = PurePosixPath(relative)
    if parts.is_absolute() or '..' in parts.parts or not parts.parts:
        raise ValueError('Unsafe relative path: ' + relative)
    target = base.joinpath(*parts.parts)
    if not target.resolve().is_relative_to(base.resolve()):
        raise ValueError('Path leaves its root: ' + relative)
    if target.is_symlink():
        raise ValueError('Refusing symlink: ' + relative)
    return target


def run(*args):
    return subprocess.run(args, check=True, text=True, capture_output=True).stdout.strip()


def source_checkout(manifest, path, apply):
    repo_url = manifest['upstream']['repo']
    repo = repo_url.rstrip('/').removesuffix('.git').split('github.com/')[1]
    tag = latest_release(repo)
    if not tag:
        raise ValueError('No stable upstream release: ' + repo)
    commit = tag_commit(repo, tag)
    if path.exists():
        run('git', '-C', str(path), 'diff', '--exit-code', 'HEAD', '--', 'skills', 'optional-skills', 'LICENSE')
        if run('git', '-C', str(path), 'rev-parse', 'HEAD') == commit:
            return path
    if not apply:
        return None
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        run('git', 'init', str(path))
        run('git', '-C', str(path), 'remote', 'add', 'origin', repo_url)
    run('git', '-C', str(path), 'fetch', '--depth=1', repo_url, 'refs/tags/' + tag)
    if run('git', '-C', str(path), 'rev-parse', 'FETCH_HEAD^{commit}') != commit:
        raise ValueError('Upstream release changed during resolution')
    run('git', '-C', str(path), 'checkout', '--detach', commit)
    return path


def bundle(folder):
    if not (folder / 'SKILL.md').is_file():
        raise ValueError('Missing SKILL.md: ' + str(folder))
    files = {}
    for p in folder.rglob('*'):
        if '.git' in p.parts or '__pycache__' in p.parts:
            continue
        if p.is_symlink():
            raise ValueError('Refusing source symlink: ' + str(p))
        if p.is_file():
            files[p.relative_to(folder).as_posix()] = p
    return files


def existing_names(home):
    names = {}
    for p in (home / 'skills').rglob('SKILL.md'):
        match = re.search(r'^name:\s*[\"\']?([^\"\'\n]+)', p.read_text(), re.M)
        if match:
            name = match.group(1).strip()
            if name in names:
                raise ValueError('Existing duplicate skill name: ' + name)
            names[name] = p.parent
    return names


def install(manifest, home, source, apply=False):
    names = [s['name'] for s in manifest['skills']]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate manifest skill names')
    existing = existing_names(home)
    plan = []
    prepared = []
    for skill in manifest['skills']:
        destination = within(home, skill['install_path'])
        if skill['name'] in existing:
            destination = existing[skill['name']]
            if not destination.resolve().is_relative_to(home.resolve()):
                raise ValueError('Existing skill leaves target home')
        base = ROOT if skill['source_kind'] == 'local' else source
        if base is None:
            plan.append({'name': skill['name'], 'status': 'source-needed', 'path': skill['install_path']})
            continue
        files = bundle(within(base, skill['source_path']))
        if skill['source_kind'] == 'upstream':
            files['_UPSTREAM_LICENSE'] = base / 'LICENSE'
            if not files['_UPSTREAM_LICENSE'].is_file():
                raise ValueError('Missing upstream license')
        elif (ROOT / 'LICENSE').is_file():
            files['_SETUP_LICENSE'] = ROOT / 'LICENSE'
        for relative in files:
            within(destination, relative)
        if destination.exists():
            # License attachments may be new; existing skills are never changed.
            comparable = {r: p for r, p in files.items() if not r.startswith('_')}
            same = all((destination / r).is_file() and (destination / r).read_bytes() == p.read_bytes()
                       for r, p in comparable.items())
            status = 'unchanged' if same else 'conflict'
        else:
            status = 'add'
        plan.append({'name': skill['name'], 'status': status, 'path': skill['install_path']})
        prepared.append((destination, files, status))
    conflicts = [p for p in plan if p['status'] == 'conflict']
    if apply and (conflicts or any(p['status'] == 'source-needed' for p in plan)):
        raise ValueError('Preflight failed; no skills were copied: ' + ', '.join(p['name'] for p in conflicts))
    if apply:
        for destination, files, status in prepared:
            if status != 'add':
                continue
            destination.mkdir(parents=True)
            for relative, origin in files.items():
                output = within(destination, relative)
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(origin, output)
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Add missing skills; default is preview')
    parser.add_argument('--home', type=Path, default=Path(os.environ.get('HERMES_HOME', str(Path.home() / '.hermes'))))
    parser.add_argument('--source', type=Path, default=ROOT / '.local' / 'upstream')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    source = source_checkout(manifest, args.source.expanduser().resolve(), args.apply)
    plan = install(manifest, args.home.expanduser().resolve(), source, args.apply)
    counts = {status: sum(p['status'] == status for p in plan) for status in sorted({p['status'] for p in plan})}
    print(json.dumps({'applied': args.apply, 'count': len(plan), 'counts': counts, 'skills': plan}, ensure_ascii=False, indent=2))
    if any(p['status'] == 'conflict' for p in plan):
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
