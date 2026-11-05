"""Daily hygiene for Discord project channels and the Hermes Desktop sidebar.

1. Attach Discord sessions with no workspace to their project folder (so the sidebar
   groups them under the project instead of Home).
2. Discord: in each project channel, delete threads idle > IDLE_DAYS, keeping the newest
   KEEP threads. Threads used as cron delivery targets are never deleted.
3. Hermes: per sidebar group (each project + Home), keep the newest CHAT_KEEP chats whatever
   their age; permanently delete every other chat (archived included) idle > CHAT_MAX_DAYS. Only chats the user
   actually had count toward CHAT_KEEP: cron/kanban/oneshot run records, delegated "Subagent:" chats and empty (0-message) chats are deleted
   once idle > RECENT_GRACE.
   Pinned chats and cron-alarm thread sessions are skipped.

Usage: python3 discord-project-hygiene.py [--dry-run]
Prints nothing when there is nothing to do (silent cron run).
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HOME = Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes")
sys.path.insert(0, str(HOME / "hermes-agent"))
# The cron interpreter is the bare bundled Python; borrow the Hermes venv's packages
# (the install hash changes on update, so pick the newest venv that has ruamel).
_venvs = sorted(HOME.glob("installs/*/environments/*/venv/lib/python3*/site-packages"),
                key=lambda p: p.stat().st_mtime, reverse=True)
for _sp in _venvs:
    if (_sp / "ruamel").is_dir():
        sys.path.insert(1, str(_sp))
        break

IDLE_DAYS = 3        # Discord threads: idle days before deletion
KEEP = 3             # Discord threads kept per channel
CHAT_KEEP = 3        # sidebar chats kept per project (newest), kept whatever their age
CHAT_MAX_DAYS = 3    # chats outside the newest CHAT_KEEP (archived included) idle longer are deleted
RECENT_GRACE = 2 * 3600  # automated runs / empty chats active this recently are left alone
AUTOMATED_SOURCES = {"cron", "kanban", "oneshot"}  # run records, not chats the user had
DRY = "--dry-run" in sys.argv
DISCORD_EPOCH_MS = 1420070400000
API = "https://discord.com/api/v10"


def env_value(key: str) -> str:
    for line in (HOME / ".env").read_text().splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit(f"{key} missing in .env")


TOKEN = env_value("DISCORD_BOT_TOKEN")


def api(method: str, path: str):
    req = urllib.request.Request(API + path, method=method, headers={
        "Authorization": "Bot " + TOKEN, "User-Agent": "DiscordBot (hermes-hygiene, 1)"})
    for _ in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read()
                return r.status, (json.loads(body) if body else None)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(float(json.loads(e.read() or b"{}").get("retry_after", 1)) + 0.2)
                continue
            return e.code, e.read().decode(errors="replace")[:200]
    return 429, "rate limited"


def snowflake_ts(sid: str | None) -> float:
    return ((int(sid) >> 22) + DISCORD_EPOCH_MS) / 1000 if sid else 0.0


def channel_folders() -> dict[str, str]:
    """channel id -> project folder, parsed from discord.channel_prompts in config.yaml."""
    from hermes_cli.config import load_config
    prompts = (load_config().get("discord") or {}).get("channel_prompts") or {}
    out = {}
    for cid, text in prompts.items():
        m = re.search(r"\(folder: (.+?)\)", str(text))
        if m:
            out[str(cid)] = m.group(1)
    return out


def protected_threads() -> set[str]:
    jobs = json.loads((HOME / "cron" / "jobs.json").read_text())
    jobs = jobs.get("jobs", jobs) if isinstance(jobs, dict) else jobs
    ids = set()
    for job in jobs:
        for key in ("deliver", "failure_deliver"):
            parts = str(job.get(key) or "").split(":")
            if len(parts) >= 3 and parts[0] == "discord":
                ids.add(parts[2])
    return ids


def guild_id(any_channel: str) -> str:
    status, ch = api("GET", f"/channels/{any_channel}")
    if status != 200:
        raise SystemExit(f"Discord 채널 조회 실패 ({status}): {ch}")
    return ch["guild_id"]


def channel_threads(cid: str, active: list[dict]) -> list[dict]:
    threads = [t for t in active if t.get("parent_id") == cid]
    before = None
    while True:
        q = f"/channels/{cid}/threads/archived/public?limit=100" + (f"&before={before}" if before else "")
        status, page = api("GET", q)
        if status != 200:
            break
        threads += page.get("threads", [])
        if not page.get("has_more") or not page.get("threads"):
            break
        before = page["threads"][-1]["thread_metadata"]["archive_timestamp"]
    return threads


def _clear_finished_ledgers(sid: str) -> bool:
    """Drop finished runtime-ledger rows (left by a newer Hermes) for ``sid`` and its compression
    chain so the delete guard trigger lets the session go. Rows still queued/started/running stay,
    which keeps the guard in force for live work. Returns True when any row was removed."""
    with sqlite3.connect(HOME / "state.db", timeout=30) as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"session_admissions", "worker_executions"} <= tables:
            return False
        chain = {sid}
        frontier = [sid]
        while frontier:  # parents and children linked through parent_session_id
            cur = frontier.pop()
            for (other,) in conn.execute(
                    "SELECT id FROM sessions WHERE parent_session_id = ? "
                    "UNION SELECT parent_session_id FROM sessions WHERE id = ? AND parent_session_id IS NOT NULL",
                    (cur, cur)):
                if other not in chain:
                    chain.add(other)
                    frontier.append(other)
        ph = ",".join("?" * len(chain))
        ids = tuple(chain)
        execs = [r[0] for r in conn.execute(
            f"SELECT execution_id FROM worker_executions WHERE session_id IN ({ph}) "
            "AND status IN ('terminal','unknown')", ids)]
        n = 0
        if execs and "worker_receipts" in tables:
            eph = ",".join("?" * len(execs))
            conn.execute(f"DELETE FROM worker_receipts WHERE execution_id IN ({eph})", execs)
        if execs:
            eph = ",".join("?" * len(execs))
            n += conn.execute(f"DELETE FROM worker_executions WHERE execution_id IN ({eph})", execs).rowcount
        n += conn.execute(
            f"DELETE FROM session_admissions WHERE target_session_id IN ({ph}) "
            "AND status IN ('terminal','unknown')", ids).rowcount
        return n > 0


def main() -> None:
    from hermes_state import SessionDB
    from hermes_state_maintenance import _LAST_ACTIVE_SQL, _not_pinned_sql
    from hermes_cli import projects_db as pdb

    lines: list[str] = []
    now = time.time()
    cutoff = now - IDLE_DAYS * 86400
    folders = channel_folders()
    db = SessionDB()

    # 1. Backfill workspace for Discord sessions.
    attached = 0
    for sid, origin in db._read_all(
            "SELECT id, origin_json FROM sessions WHERE source = 'discord' AND COALESCE(cwd, '') = ''"):
        o = json.loads(origin or "{}")
        folder = folders.get(str(o.get("parent_chat_id") or "")) or folders.get(str(o.get("chat_id") or ""))
        if folder:
            attached += 1
            if not DRY:
                db.update_session_cwd(sid, folder)
    if attached:
        lines.append(f"- 프로젝트로 연결한 디스코드 채팅: {attached}개")

    # 2. Discord thread cleanup.
    keep_ids = protected_threads()
    gid = guild_id(next(iter(folders)))
    status, active = api("GET", f"/guilds/{gid}/threads/active")
    active_threads = active.get("threads", []) if status == 200 else []
    deleted, failed = [], []
    home_channel = env_value("DISCORD_HOME_CHANNEL")  # Desktop chats outside a project report here
    for cid in [*folders, home_channel]:
        threads = [t for t in channel_threads(cid, active_threads) if t["id"] not in keep_ids]
        for t in threads:
            t["_last"] = max(snowflake_ts(t.get("last_message_id")), snowflake_ts(t["id"]))
        threads.sort(key=lambda t: t["_last"], reverse=True)
        for t in threads[KEEP:]:
            if t["_last"] >= cutoff:
                continue
            if DRY:
                deleted.append(t["name"])
                continue
            s, body = api("DELETE", f"/channels/{t['id']}")
            (deleted if s in (200, 204) else failed).append(t["name"] if s in (200, 204) else f"{t['name']} ({s})")
    if deleted:
        lines.append(f"- 디스코드 스레드 삭제{' 예정' if DRY else ''}: {len(deleted)}개 ({', '.join(deleted[:10])})")
    if failed:
        lines.append(f"- 디스코드 스레드 삭제 실패: {len(failed)}개 ({', '.join(failed[:10])})"
                     " — 봇 역할에 '스레드 관리' 권한이 필요합니다.")

    # 3. Hermes sidebar cleanup: per group keep the newest CHAT_KEEP visible chats; delete any other
    #    chat (archived included) idle > CHAT_MAX_DAYS.
    chat_cutoff = now - CHAT_MAX_DAYS * 86400
    protected_sessions = {r[0] for r in db._read_all(
        "SELECT id FROM sessions WHERE source = 'discord' AND thread_id IN (%s)" % ",".join("?" * len(keep_ids)),
        tuple(keep_ids))} if keep_ids else set()
    rows = db._read_all(
        f"""SELECT s.id, s.cwd, {_LAST_ACTIVE_SQL} AS last_active, s.archived, s.source,
                   COALESCE(s.message_count, 0) AS msgs, COALESCE(s.title, '') AS title FROM sessions s
            WHERE COALESCE(s.end_reason, '') <> 'compression'
              AND s.source <> 'subagent'
              AND COALESCE(s.hidden, 0) = 0 AND {_not_pinned_sql()}""")
    groups: dict[str, list] = {}
    doomed: list[str] = []
    with sqlite3.connect(HOME / "projects.db") as pconn:
        pconn.row_factory = sqlite3.Row
        for sid, cwd, last, archived, source, msgs, title in rows:
            last = float(last or 0)
            if source in AUTOMATED_SOURCES or msgs == 0 or title.startswith("Subagent:"):
                if last < now - RECENT_GRACE:   # recent ones may still be running or just opened
                    doomed.append(sid)          # scheduled-run records and empty chats are never kept
                continue                        # either way they never take a keep slot
            if archived:
                if last < chat_cutoff:      # archived chats never take a keep slot
                    doomed.append(sid)
            else:
                proj = pdb.project_for_path(pconn, cwd) if cwd else None
                groups.setdefault(proj.id if proj else "home", []).append((last, sid))
    for items in groups.values():
        items.sort(reverse=True)
        doomed += [sid for last, sid in items[CHAT_KEEP:] if last < chat_cutoff]
    doomed = [s for s in dict.fromkeys(doomed) if s not in protected_sessions]
    removed, busy = 0, 0
    busy_reasons: dict[str, int] = {}
    for sid in doomed:
        if DRY:
            removed += 1
            continue
        for attempt in (1, 2):
            try:
                removed += db.delete_sessions([sid], sessions_dir=HOME / "sessions",
                                              exclude_active_write_guards=True, include_compression_chain=True) > 0
                break
            except sqlite3.IntegrityError as exc:
                # A newer Hermes (run Oct 14-19) left gateway runtime ledgers plus a delete-guard
                # trigger in state.db; the current release never clears them, so finished ledger
                # rows are cleared here and the delete retried once.
                if attempt == 1 and "runtime history" in str(exc) and _clear_finished_ledgers(sid):
                    continue
                reason = str(exc).split(":")[0][:60]
                busy_reasons[reason] = busy_reasons.get(reason, 0) + 1
                busy += 1
                break
            except Exception as exc:  # mid-turn or locked: retried on the next run
                reason = f"{type(exc).__name__}: {str(exc)[:60]}"
                busy_reasons[reason] = busy_reasons.get(reason, 0) + 1
                busy += 1
                break
    if removed:
        lines.append(f"- 왼쪽 채팅 삭제{' 예정' if DRY else ''}: {removed}개 (프로젝트별 최근 {CHAT_KEEP}개 유지, 나머지 중 {CHAT_MAX_DAYS}일 경과분 보관 포함 삭제)")
    if busy:
        detail = ", ".join(f"{r} {n}개" for r, n in busy_reasons.items())
        lines.append(f"- 삭제 못 해 다음에 재시도: {busy}개 ({detail})")

    if lines:
        print(("[미리보기] " if DRY else "") + "채널·채팅 정리")
        print("\n".join(lines))


if __name__ == "__main__":
    main()
