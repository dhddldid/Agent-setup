#!/usr/bin/env python3
"""Resolve a GitHub repository's latest stable release and optional commit."""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request


def validate_repo(repo: str) -> str:
    """Require an owner/repo identifier before making network requests."""
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
        raise ValueError('Expected a GitHub owner/repo identifier')
    return repo


def latest_release(repo: str) -> str | None:
    """Return GitHub's latest stable tag, or None for HTTP 404 (no release).

    Use the public releases/latest redirect by default and the authenticated
    API when GITHUB_TOKEN is set. Other network failures propagate to callers.
    """
    validate_repo(repo)
    token = os.environ.get('GITHUB_TOKEN')
    url = (f'https://api.github.com/repos/{repo}/releases/latest' if token
           else f'https://github.com/{repo}/releases/latest')
    headers = {'User-Agent': 'agent-setup'}
    if token:
        headers['Accept'] = 'application/vnd.github+json'
        headers['Authorization'] = f'Bearer {token}'
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
                release = json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            raise
        if release.get('draft') or release.get('prerelease'):
            raise ValueError('GitHub returned a non-stable release')
        return release['tag_name']
    # Read the redirect target without following it: /releases/tag/<tag> names
    # the latest release, /releases (no tag) means the repository has none.
    try:
        with _open_public(urllib.request.Request(url, headers=headers)) as response:
            target = response.geturl()
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        if error.code not in (301, 302, 303, 307, 308):
            raise
        target = urllib.parse.urljoin(url, error.headers.get('Location', ''))
    path = urllib.parse.urlsplit(target).path.rstrip('/')
    if path.lower() == f'/{repo}/releases'.lower():
        return None
    prefix = f'/{repo}/releases/tag/'
    if not path.lower().startswith(prefix.lower()):
        raise ValueError(f'Unexpected latest-release redirect: {target}')
    tag = urllib.parse.unquote(path[len(prefix):])
    if not tag:
        raise ValueError('GitHub returned an empty release tag')
    return tag


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _open_public(request: urllib.request.Request):
    """Open a public GitHub URL and surface redirects as HTTPError."""
    return urllib.request.build_opener(_NoRedirect).open(request, timeout=30)


def tag_commit(repo: str, tag: str) -> str:
    """Resolve an exact tag, preferring the peeled commit of annotated tags."""
    validate_repo(repo)
    ref = f'refs/tags/{tag}'
    result = subprocess.run(
        ['git', 'ls-remote', '--tags', f'https://github.com/{repo}.git', ref, ref + '^{}'],
        capture_output=True, text=True, check=True, timeout=60,
    )
    refs = dict(line.split('\t', 1)[::-1] for line in result.stdout.splitlines() if line)
    commit = refs.get(ref + '^{}') or refs.get(ref)
    if not commit or not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError(f'Unable to resolve release tag {repo}@{tag}')
    return commit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', help='GitHub owner/repo')
    parser.add_argument('--commit', action='store_true', help='Also resolve the tag commit')
    parser.add_argument('--json', action='store_true', help='Print repo, tag, commit, and status as JSON')
    args = parser.parse_args(argv)
    try:
        tag = latest_release(args.repo)
        commit = tag_commit(args.repo, tag) if tag and args.commit else None
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f'latest_release: {error}', file=sys.stderr)
        return 1
    status = 'ok' if tag else 'no_release'
    if args.json:
        print(json.dumps({'repo': args.repo, 'tag': tag, 'commit': commit, 'status': status}))
    else:
        print(f'{tag} {commit}' if commit else tag or status)
    return 0


if __name__ == '__main__':
    sys.exit(main())
