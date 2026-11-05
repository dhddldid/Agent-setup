#!/usr/bin/env python3
"""Report installed components versus latest stable releases and reject inventory pins.

Installed versions and skill-copy provenance are observations. Tag-specific local
patches remain under hermes/patches. Exit 1 for inventory pins or lookup failures;
available updates and missing patch bundles are reported for the updater preflight.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.latest_release import latest_release

ROOT = Path(__file__).resolve().parents[1]
INVENTORIES = ('hermes/manifest.json', 'codex/inventories/tools.lock.json',
               'codex/inventories/external-skills.json')
PIN_FIELDS = {'commit', 'reference_commit', 'version', 'ref', 'releaseTag',
              'skillFolderHash', 'tag', 'revision', 'pinned_version'}


def load(path):
    return json.loads(path.read_text())


def slug(url):
    return url.rstrip('/').removesuffix('.git').split('github.com/')[1]


def inventory_pins(root=ROOT):
    """Return every forbidden field, including fields with empty values."""
    found = []

    def visit(value, location):
        if isinstance(value, dict):
            for key, child in value.items():
                target = f'{location}.{key}'
                if key in PIN_FIELDS:
                    found.append(target)
                visit(child, target)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f'{location}[{index}]')

    for name in INVENTORIES:
        visit(load(root / name), name)
    return found


def command_output(*args):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as error:
        return None, str(error)
    if result.returncode:
        return None, (result.stderr.strip() or result.stdout.strip() or
                      f'exit {result.returncode}')
    return result.stdout.strip(), None


def version_from(text):
    match = re.search(r'\bv?(\d+\.\d+\.\d+(?:[-+][\w.-]+)?)', text or '')
    return match.group(1) if match else None


def omh_version(home):
    state = home / '.local/share/omh/self-update.json'
    if state.is_file():
        value = load(state).get('active', {}).get('version')
        if value:
            return value, str(state), None
    output, error = command_output('omh', '--version')
    return version_from(output), 'omh --version', error


def installed_skill_copy(root, home, source):
    """Infer copy provenance only when every installed bundle matches the source."""
    folders = sorted(path for path in (root / 'shared/skills/omh').iterdir()
                     if path.is_dir() and (path / 'SKILL.md').is_file())
    matched = 0
    missing = []
    changed = []
    for folder in folders:
        target = home / folder.name
        if not (target / 'SKILL.md').is_file():
            missing.append(folder.name)
            continue
        files = [p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
        if all((target / p.relative_to(folder)).is_file() and
               (target / p.relative_to(folder)).read_bytes() == p.read_bytes() for p in files):
            matched += 1
        else:
            changed.append(folder.name)
    complete = bool(folders) and not missing and not changed
    return {'installed': source.get('version') if complete else None,
            'evidence': str(home), 'matched_skills': matched,
            'expected_skills': len(folders), 'missing_skills': missing,
            'changed_skills': changed,
            'copy_status': 'matched' if complete else 'missing' if len(missing) == len(folders) else 'mixed'}


def installed_components(root=ROOT, home=None):
    home = home or Path.home()
    hermes_home = Path(os.environ.get('HERMES_HOME', str(home / '.hermes')))
    manifest = load(root / 'hermes/manifest.json')
    source = load(root / 'shared/skills/omh/SOURCE.json')
    output, error = command_output('hermes', '--version')
    rows = [{'component': 'Hermes', 'repo': slug(manifest['upstream']['repo']),
             'installed': version_from(output), 'evidence': 'hermes --version',
             'observation_error': error, 'patch_target': 'hermes-agent'}]
    version, evidence, error = omh_version(home)
    rows.append({'component': 'OMH runtime', 'repo': slug(manifest['omh']['repo']),
                 'installed': version, 'evidence': evidence, 'observation_error': error})
    for plugin in manifest['plugins']:
        path = hermes_home / 'plugins' / plugin['name']
        output, error = command_output('git', '-C', str(path), 'describe', '--tags', '--always')
        rows.append({'component': plugin['name'], 'repo': slug(plugin['repo']),
                     'installed': output, 'evidence': str(path), 'observation_error': error,
                     'patch_target': plugin['name']})
    repo = slug(source['upstream'])
    rows.append({'component': 'OMH repository skill copy', 'repo': repo,
                 'installed': source.get('version'), 'evidence': 'shared/skills/omh/SOURCE.json'})
    for label, skill_home in [('Claude', home / '.claude/skills'), ('Codex', home / '.agents/skills')]:
        rows.append({'component': f'OMH {label} installed skills', 'repo': repo,
                     **installed_skill_copy(root, skill_home, source)})
    return rows


def release_status(installed, tag):
    if not tag:
        return 'no_release'
    if not installed:
        return 'unknown'
    # git describe distance suffixes and prerelease suffixes remain significant.
    return 'current' if installed.removeprefix('v') == tag.removeprefix('v') else 'different'


def report(root=ROOT, home=None):
    pins = inventory_pins(root)
    rows = installed_components(root, home)
    cache = {}
    for row in rows:
        repo = row['repo']
        if repo not in cache:
            try:
                cache[repo] = (latest_release(repo), None)
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                cache[repo] = (None, str(error))
        tag, error = cache[repo]
        row.update(latest_tag=tag, status='error' if error else release_status(row['installed'], tag))
        if error:
            row['release_error'] = error
        target = row.pop('patch_target', None)
        if target:
            patch = root / 'hermes/patches' / target / f'{tag}.patch' if tag else None
            row['latest_patch'] = str(patch.relative_to(root)) if patch else None
            row['latest_patch_exists'] = patch.is_file() if patch else None
    return {'inventory_pins': pins, 'components': rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = report()
    except (OSError, ValueError, KeyError) as error:
        print(f'check_releases: {error}', file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for row in result['components']:
            detail = f"; copy={row['copy_status']} ({row['matched_skills']}/{row['expected_skills']})" if 'copy_status' in row else ''
            if 'latest_patch_exists' in row:
                detail += f"; latest patch={'present' if row['latest_patch_exists'] else 'missing'} ({row['latest_patch']})"
            error = row.get('release_error') or row.get('observation_error')
            if error:
                detail += f'; {error}'
            print(f"{row['status']:<10} {row['component']}: installed {row['installed'] or 'unknown'} / latest stable {row['latest_tag'] or 'unavailable'}{detail}")
        for pin in result['inventory_pins']:
            print(f'ERROR inventory pin: {pin}')
        if not result['inventory_pins']:
            print('PASS: repository inventories follow runtime latest-stable resolution')
    return int(bool(result['inventory_pins']) or any(
        row['status'] == 'error' or row.get('observation_error') for row in result['components']))


if __name__ == '__main__':
    sys.exit(main())
