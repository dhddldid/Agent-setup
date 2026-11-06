#!/usr/bin/env python3
"""LLM 호출 없이 라우팅·위임 이력을 검사한다 (Python 3.12+).

single_later_*는 뒤에 위임이 더 관측된 단일 작업 호출 수다.
작업 간 의존성·동시 실행 가능성은 사람이 보고서로 검토한다.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import tempfile
import sqlite3
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
PARALLEL = {"dag-ulw", "ultrawork", "ultragoal", "ulw-work", "ulw-loop"}


def decode(value, default):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return default
    return value if value is not None else default


def hint_source(payload):
    """The selected hint's rule id identifies the last-resort pack bridge."""
    if not payload.get("selected_workflow"):
        return "none"
    hints = payload.get("hints", [])
    return "user-pack" if hints and hints[0].get("id") == "user_trigger_pack" else "shipped-rule"


# Load the installed plugin under its Hermes namespace without running its host
# registration __init__. The OMH CLI shebang selects the venv with omh installed.
# On this host that is ~/.local/share/omh/generations/<generation>/venv/bin/python.
HINT_WORKER = r"""
import importlib, json, pathlib, sys, types
import omh
plugin = pathlib.Path(sys.argv[1])
for name, path in (("hermes_plugins", plugin.parent), ("hermes_plugins.omh", plugin)):
    package = types.ModuleType(name)
    package.__path__ = [str(path)]
    sys.modules[name] = package
awareness = importlib.import_module("hermes_plugins.omh.awareness")
texts = json.load(sys.stdin)
print(json.dumps([awareness.awareness_route_hint(text) for text in texts]))
"""


def measure_route_hints(texts, env, omh="omh", hint_function=None):
    if hint_function is not None:
        return [hint_function(text) for text in texts], "injected"
    executable = shutil.which(omh)
    if not executable:
        raise RuntimeError(f"OMH CLI not found: {omh}")
    first = Path(executable).read_text().splitlines()[0]
    interpreter = os.environ.get("OMH_HINT_PYTHON") or (first[2:] if first.startswith("#!/") else "")
    if not interpreter or not Path(interpreter).is_file():
        raise RuntimeError("Set OMH_HINT_PYTHON to the Python interpreter that imports omh")
    plugin = Path.home() / ".hermes/plugins/omh"
    result = subprocess.run([interpreter, "-c", HINT_WORKER, str(plugin)],
                            input=json.dumps(texts), env=env, capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)
    return json.loads(result.stdout), interpreter


def routing(corpus, omh="omh", max_multi_misses=0, max_small_misses=0,
            pack=None, hint_function=None):
    """Measure the actual Route Hint; recommend top-1 is secondary evidence."""
    data = json.loads(Path(corpus).read_text())
    if data.get("schema_version") != "ko_routing_corpus/v1" or not data.get("cases"):
        raise ValueError("ko_routing_corpus/v1의 cases가 필요합니다")
    for case in data["cases"]:
        if (case.get("kind") not in {"multi", "small"}
                or not isinstance(case.get("text"), str)
                or (case["kind"] == "multi" and (not isinstance(case.get("expect_any"), list) or not case["expect_any"]))):
            raise ValueError("각 사례에 kind와 text, multi 사례에 expect_any 배열이 필요합니다")
    pack = Path(pack) if pack is not None else ROOT / "hermes/omh/trigger-packs/ko.json"
    scratch = Path.home() / ".hermes/cache/scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    checked, misses = [], []
    with tempfile.TemporaryDirectory(prefix="omh-route-measure-", dir=scratch) as temporary:
        home = Path(temporary)
        target = home / "omh/routing/trigger-packs/ko.json"
        target.parent.mkdir(parents=True)
        shutil.copyfile(pack, target)
        (home / "hermes").mkdir()
        env = {**os.environ, "OMH_HOME": str(home / "omh"), "HERMES_HOME": str(home / "hermes")}
        hints, interpreter = measure_route_hints([c["text"] for c in data["cases"]], env, omh, hint_function)
        if len(hints) != len(data["cases"]):
            raise RuntimeError("Route Hint result count differs from corpus")
        for case, hint in zip(data["cases"], hints):
            skill = hint.get("selected_workflow", "")
            source = hint_source(hint)
            result = subprocess.run([omh, "recommend", case["text"], "--limit", "1", "--json"],
                                    env=env, capture_output=True, text=True, timeout=60)
            if result.returncode:
                raise RuntimeError(result.stderr or result.stdout)
            recommendations = json.loads(result.stdout).get("recommendations", [])
            top1 = recommendations[0]["skill"] if recommendations else ""
            failed = skill not in case["expect_any"] if case["kind"] == "multi" else skill in PARALLEL
            classification = ("small-false-positive" if case["kind"] == "small" and failed else
                              "shipped-rule-claimed" if failed and source == "shipped-rule" else
                              "miss" if failed else "hit")
            row = {**case, "actual": skill, "selected_workflow": skill, "source": source,
                   "recommend_top1": top1, "classification": classification}
            checked.append(row)
            if failed:
                misses.append(row)
    multi_total = sum(c["kind"] == "multi" for c in checked)
    small_total = len(checked) - multi_total
    multi_misses = sum(c["kind"] == "multi" for c in misses)
    small_misses = len(misses) - multi_misses
    multi_hits = multi_total - multi_misses
    return {"command": "routing", "cases": len(checked), "multi_total": multi_total,
            "multi_hits": multi_hits, "multi_hit_rate": multi_hits / multi_total if multi_total else 0,
            "small_total": small_total, "small_fp_rate": small_misses / small_total if small_total else 0,
            "shipped_rule_claimed": sum(c["classification"] == "shipped-rule-claimed" for c in checked),
            "multi_misses": multi_misses, "small_misses": small_misses,
            "findings": len(misses), "misses": misses, "results": checked,
            "hint_interpreter": interpreter, "pack": str(pack),
            "threshold_exceeded": multi_misses > max_multi_misses or small_misses > max_small_misses}

def summarize(events, titles):
    sessions = []
    for sid, rows in events.items():
        spawns = [r for r in rows if r["tasks"]]
        if not spawns:
            continue
        single = [r for r in spawns if r["tasks"] == 1]
        later_session = sum(any(s["order"] > r["order"] for s in spawns) for r in single)
        later_turn = sum(any(s["order"] > r["order"] and s["user_id"] == r["user_id"] for s in spawns) for r in single)
        sessions.append({"id": sid, "title": titles.get(sid) or "(제목 없음)",
                         "spawns": len(spawns), "tasks": sum(r["tasks"] for r in spawns),
                         "single_task_spawns": len(single), "single_later_turn": later_turn,
                         "single_later_session": later_session,
                         "dag_ulw_loaded": any(r["dag"] for r in rows),
                         "user_message_ids": list(dict.fromkeys(r["user_id"] for r in spawns if r["user_id"] is not None))})
    sessions.sort(key=lambda r: (r["single_later_turn"], r["single_later_session"], r["spawns"]), reverse=True)
    totals = {key: sum(r[key] for r in sessions) for key in
              ("spawns", "tasks", "single_task_spawns", "single_later_turn", "single_later_session")}
    totals.update(sessions=len(sessions), dag_ulw_sessions=sum(r["dag_ulw_loaded"] for r in sessions))
    totals["findings"] = sum(bool(r["single_later_session"] or not r["dag_ulw_loaded"]) for r in sessions)
    return {"status": "covered", "summary": totals, "sessions": sessions}


def hermes_history(db, cutoff):
    events, titles = defaultdict(list), {}
    # URI read-only는 누락 DB의 자동 생성도 막는다.
    with sqlite3.connect(Path(db).expanduser().resolve().as_uri() + "?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        titles = {r["id"]: r["title"] for r in conn.execute("SELECT id, title FROM sessions")}
        users = {}
        for row in conn.execute("SELECT id, session_id, role, tool_calls, timestamp FROM messages ORDER BY timestamp, id"):
            sid = row["session_id"]
            if row["role"] == "user":
                users[sid] = row["id"]
            calls = decode(row["tool_calls"], [])
            if not isinstance(calls, list):
                continue
            for index, call in enumerate(calls):
                function = call.get("function", {})
                name = function.get("name", call.get("name"))
                args = decode(function.get("arguments", call.get("arguments")), {})
                if not isinstance(args, dict):
                    continue
                tasks = 0
                if row["timestamp"] >= cutoff and name == "delegate_task" and args.get("action", "spawn") == "spawn":
                    tasks = len(args["tasks"]) if isinstance(args.get("tasks"), list) else int(bool(args.get("goal")))
                dag = name == "skill_view" and args.get("name") == "dag-ulw"
                if tasks or dag:
                    events[sid].append({"tasks": tasks, "dag": dag, "user_id": users.get(sid), "order": (row["id"], index)})
    return summarize(events, titles)


def timestamp(value):
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return 0
    return 0


def log_lines(path):
    with path.open(encoding="utf-8", errors="replace") as stream:
        yield from stream


def external_history(base, cutoff, runner):
    """확인 가능한 Task/Agent, spawn_agent 블록만 집계한다."""
    events, titles = defaultdict(list), {}
    observed = 0
    for path in sorted(Path(base).expanduser().rglob("*.jsonl")):
        # 하위 에이전트 자체 로그는 부모와 중복 집계하지 않는다.
        if "subagents" in path.parts:
            continue
        sid, user, order = path.stem, None, 0
        for line in log_lines(path):
            row = decode(line, {})
            if not isinstance(row, dict):
                continue
            order += 1
            blocks = []
            if runner == "claude":
                message = row.get("message", {})
                if not isinstance(message, dict):
                    continue
                if message.get("role") == "user":
                    user = row.get("uuid", order)
                if message.get("role") == "assistant" and isinstance(message.get("content"), list):
                    blocks = [b for b in message["content"] if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") in {"Task", "Agent"}]
            else:
                payload = row.get("payload", {})
                if not isinstance(payload, dict):
                    continue
                if row.get("type") == "event_msg" and payload.get("type") == "user_message":
                    user = row.get("id", order)
                if row.get("type") == "response_item" and payload.get("type") == "function_call" and payload.get("name") == "spawn_agent":
                    blocks = [payload]
            observed += len(blocks)
            if timestamp(row.get("timestamp")) < cutoff:
                continue
            if blocks:
                # Claude는 한 assistant 메시지의 Task/Agent 묶음을 한 dispatch로 센다.
                events[sid].append({"tasks": len(blocks), "dag": False, "user_id": user, "order": (order, 0)})
    if not observed:
        return {"status": "not covered", "reason": "확인 가능한 하위 에이전트 spawn 기록 없음"}
    result = summarize(events, titles)
    # dag-ulw 로딩은 Hermes 전용 지표다.
    result["summary"]["findings"] = sum(bool(r["single_later_session"]) for r in result["sessions"])
    result["dag_ulw_coverage"] = "not covered"
    return result


def history(days, db, claude, codex, now=None):
    cutoff = (time.time() if now is None else now) - days * 86400
    runners = {"Hermes": hermes_history(db, cutoff),
               "Claude Code": external_history(claude, cutoff, "claude"),
               "Codex": external_history(codex, cutoff, "codex")}
    return {"command": "history", "days": days, "runners": runners,
            "findings": sum(r.get("summary", {}).get("findings", 0) for r in runners.values())}


def markdown(result, top=10):
    lines = ["# 병렬 실행 누락 점검", ""]
    if result["command"] == "routing":
        lines += [f"라우팅 {result['cases']}건 · 복합 요청 누락 {result['multi_misses']}건 · 소규모 과잉 라우팅 {result['small_misses']}건", ""]
        for row in result["misses"]:
            lines.append(f"- {row['kind']}: {row['text']} → `{row['actual']}` (기대: {', '.join(row.get('expect_any', ['non-parallel']))})")
    else:
        lines += [f"최근 {result['days']}일 · 검토 대상 세션 {result['findings']}개", "",
                  "뒤에 추가 위임이 관측된 단일 작업 호출을 표시합니다. 작업 의존성과 분할 사유는 원문에서 검토합니다.", "",
                  "| 실행기 | 세션 | spawn 호출 | 작업 | 단일 작업 호출 | 같은 턴 후속 | 세션 후속 | dag-ulw 세션 |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|"]
        details = []
        for name, runner in result["runners"].items():
            if runner["status"] != "covered":
                lines.append(f"| {name} | not covered | | | | | | |")
                continue
            s = runner["summary"]
            dag = s['dag_ulw_sessions'] if name == 'Hermes' else 'not covered'
            lines.append(f"| {name} | {s['sessions']} | {s['spawns']} | {s['tasks']} | {s['single_task_spawns']} | {s['single_later_turn']} | {s['single_later_session']} | {dag} |")
            details += ["", f"## {name} 상위 검토 세션", ""]
            for row in runner["sessions"][:top]:
                title = row['title'].replace('\n', ' ').replace('|', '\\|')
                details.append(f"- `{row['id']}` · {title} · 호출 {row['spawns']}, 단일 {row['single_task_spawns']}, 턴 후속 {row['single_later_turn']}, 세션 후속 {row['single_later_session']}, dag-ulw {row['dag_ulw_loaded']} · 사용자 메시지 {row['user_message_ids']}")
        lines.extend(details)
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true")
    common.add_argument("--report-file", type=Path)
    common.add_argument("--quiet-clean", action="store_true", help="발견 0건이면 stdout 생략")
    sub = parser.add_subparsers(dest="command", required=True)
    route = sub.add_parser("routing", parents=[common])
    route.add_argument("--corpus", type=Path, default=ROOT / "hermes/omh/trigger-packs/ko-corpus.json")
    route.add_argument("--omh", default="omh")
    route.add_argument("--pack", type=Path, default=ROOT / "hermes/omh/trigger-packs/ko.json")
    route.add_argument("--max-multi-misses", type=int, default=0)
    route.add_argument("--max-small-misses", type=int, default=0)
    hist = sub.add_parser("history", parents=[common])
    hist.add_argument("--days", type=int, default=3)
    hist.add_argument("--db", type=Path, default=Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")) / "state.db")
    hist.add_argument("--claude-dir", type=Path, default=Path.home() / ".claude/projects")
    hist.add_argument("--codex-dir", type=Path, default=Path.home() / ".codex/sessions")
    hist.add_argument("--top", type=int, default=10)
    args = parser.parse_args(argv)
    try:
        if args.command == "routing":
            if min(args.max_multi_misses, args.max_small_misses) < 0:
                parser.error("허용 누락 수는 0 이상이어야 합니다")
            result = routing(args.corpus, args.omh, args.max_multi_misses, args.max_small_misses, pack=args.pack)
        else:
            if args.days < 1:
                parser.error("days는 1 이상이어야 합니다")
            result = history(args.days, args.db, args.claude_dir, args.codex_dir)
        report = markdown(result, getattr(args, "top", 10))
        if args.report_file:
            args.report_file.parent.mkdir(parents=True, exist_ok=True)
            args.report_file.write_text(report, encoding="utf-8")
        if not args.quiet_clean or result["findings"]:
            print(json.dumps(result, ensure_ascii=False) if args.json else report, end="\n" if args.json else "")
        return int(result.get("threshold_exceeded", False))
    except (OSError, ValueError, RuntimeError, sqlite3.Error, subprocess.SubprocessError) as exc:
        print(f"병렬 점검 실패: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
