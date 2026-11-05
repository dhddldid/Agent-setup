"""Executor-neutral, report-first GAM lifecycle scan and authorized archive.

Run inside the installed GAM Python (PyYAML and MCP). Never edit vault files.
The archive API has no expected-version argument: read/recheck reduces races;
backend compare-and-swap remains required for strict concurrent guarantees.
"""
import argparse
import asyncio
from contextlib import asynccontextmanager
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import uuid

from lifecycle import classify, timestamp


def metadata(value, ident):
    if isinstance(value, dict):
        if value.get('id') == ident and 'status' in value:
            return value
        for child in value.values():
            result = metadata(child, ident)
            if result is not None:
                return result
    elif isinstance(value, list):
        for child in value:
            result = metadata(child, ident)
            if result is not None:
                return result
    return None


def contains_id(value, ident):
    if isinstance(value, dict):
        return (value.get('id') == ident or value.get('memory_id') == ident
                or any(contains_id(v, ident) for v in value.values()))
    if isinstance(value, list):
        return any(contains_id(v, ident) for v in value)
    return False


def body_of(value):
    if isinstance(value, dict):
        for key in ('body', 'content'):
            if isinstance(value.get(key), str):
                return value[key]
        for child in value.values():
            result = body_of(child)
            if result:
                return result
    return ''


def fingerprint(meta, body):
    payload = json.dumps([meta, body], ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def scan(vault, now, policy):
    """Read confined Markdown only. Parse failures are explicit report rows."""
    import yaml
    vault = Path(vault)
    if vault.is_symlink():
        raise ValueError('Vault root must be a real directory')
    vault = vault.resolve(strict=True)
    rows, seen = [], set()
    for current, dirs, files in os.walk(vault, followlinks=False):
        dirs[:] = [d for d in dirs if not (Path(current) / d).is_symlink()]
        for name in sorted(files):
            path = Path(current) / name
            if path.suffix != '.md' or path.is_symlink() or not path.resolve().is_relative_to(vault):
                continue
            try:
                text = path.read_text()
                if not text.startswith('---\n'):
                    continue
                _, header, body = text.split('---', 2)
                meta = yaml.safe_load(header)
                if not isinstance(meta, dict) or not meta.get('id'):
                    continue
                row = classify(meta, now, policy, body)
                if isinstance(row['version'], dt.datetime):
                    row['version'] = row['version'].isoformat()
                row.update(digest=fingerprint(meta, body), project=meta.get('project'))
                if row['id'] in seen:
                    raise ValueError('Duplicate memory ID in vault')
                seen.add(row['id'])
                rows.append(row)
            except (ValueError, OSError, yaml.YAMLError) as error:
                rows.append({'id': None, 'state': 'scan_error', 'reasons': [type(error).__name__], 'archive_eligible': False})
    return rows


@asynccontextmanager
async def connect(command, args):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    async with stdio_client(StdioServerParameters(command=command, args=args)) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            yield session

async def call(session, name, args):
    response = await session.call_tool(name, args)
    data = response.structuredContent
    if data is None:
        data = json.loads(next(c.text for c in response.content if hasattr(c, 'text')))
    if response.isError or (isinstance(data, dict) and data.get('ok') is False):
        raise RuntimeError(name + ' failed')
    return data


async def apply_rows(rows, session, now, policy, invoke=call):
    """Each write requires a fresh exact target and verified archived readback."""
    receipts = []
    for row in rows:
        if not row['archive_eligible']:
            continue
        ident = row['id']
        receipt = {'id': ident, 'outcome': 'skipped', 'reason': 'changed_or_ineligible'}
        try:
            current = await invoke(session, 'memory_get', {'id': ident})
            meta = metadata(current, ident)
            if not meta or timestamp(meta.get('updated_at')) != timestamp(row['version']) or meta.get('project') != row['project']:
                receipts.append(receipt)
                continue
            state = classify(meta, now, policy, body_of(current))
            # Compare scan metadata via lifecycle/version, then snapshot the full
            # API response immediately before the write for the audit receipt.
            if not state['archive_eligible']:
                receipts.append(receipt)
                continue
            receipt['before_digest'] = fingerprint(meta, body_of(current))
            await invoke(session, 'memory_archive', {
                'id': ident, 'request_id': str(uuid.uuid4()),
                'reason': 'Authorized GAM lifecycle TTL expiry', 'hard_delete': False})
            after = await invoke(session, 'memory_get', {'id': ident})
            archived = metadata(after, ident)
            if not archived or archived.get('status') != 'archived':
                raise RuntimeError('Archived status readback failed')
            # Explicit all-pages metadata search proves ordinary active exclusion.
            cursor = None
            while True:
                query = {'query': ident, 'project': row['project'], 'scopes': ['project'],
                         'statuses': ['active'], 'mode': 'metadata', 'cross_project': False,
                         'include_candidates': False, 'include_rejected': False,
                         'include_archived': False, 'include_superseded': False, 'limit': 100}
                if cursor:
                    query['cursor'] = cursor
                found = await invoke(session, 'memory_search', query)
                if contains_id(found, ident):
                    raise RuntimeError('Archived memory remains in active retrieval')
                cursor = found.get('next_cursor') or (found.get('data') or {}).get('next_cursor')
                if not cursor:
                    break
            receipt.update(outcome='archived', reason='archived_and_active_exclusion_verified')
        except (RuntimeError, ValueError, OSError, KeyError, TypeError) as error:
            receipt.update(outcome='failed', reason=type(error).__name__)
        receipts.append(receipt)
    return receipts


async def maintain(vault, policy, *, apply=False, config=None, gam_state=None, command=None, now=None):
    from global_memory.config import load_settings, get_platform_paths
    now = now or dt.datetime.now(dt.timezone.utc)
    paths = get_platform_paths()
    config = Path(config) if config else paths.config_file
    configured = load_settings(config).vault_path
    if Path(vault).is_symlink() or configured.resolve() != Path(vault).resolve():
        raise ValueError('Requested vault does not match GAM configuration')
    rows = scan(vault, now, policy)
    result = {'apply': apply, 'rows': rows, 'archived': 0,
              'memory_archive_candidates': sum(bool(r['archive_eligible']) for r in rows),
              'memory_review_candidates': [r['id'] for r in rows if r['state'] in ('stale', 'unknown', 'open', 'legacy_review', 'invalid')],
              'receipts': [], 'archive_cas': 'read_recheck_only'}
    if apply and result['memory_archive_candidates']:
        args = ['--direct', '--config', str(config), '--token-file', str(paths.auth_token)]
        if gam_state:
            args += ['--state', str(gam_state)]
        async with connect(command or str(Path(sys.executable).with_name('global-memory-mcp')), args) as session:
            result['receipts'] = await apply_rows(rows, session, now, policy)
        result['archived'] = sum(r['outcome'] == 'archived' for r in result['receipts'])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy', type=Path, required=True)
    parser.add_argument('--vault', type=Path)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--gam-state', type=Path)
    parser.add_argument('--command')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    from global_memory.config import load_settings, get_platform_paths
    config = args.config or get_platform_paths().config_file
    vault = args.vault or load_settings(config).vault_path
    policy = json.loads(args.policy.read_text())['gam']
    print(json.dumps(asyncio.run(maintain(vault, policy, apply=args.apply, config=config,
          gam_state=args.gam_state, command=args.command)), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
