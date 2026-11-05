#!/usr/bin/env python3
"""Weekly retention for Codex, Claude Code, Hermes, CodeGraph and GAM data.

Policy: shared/retention/policy.json. Every item deletes entries older than its
`days`, always keeping the newest `keep_latest` entries. Executors' own retention
settings (Hermes state.db, Claude transcripts) are set with `configure`.

  python3 scripts/retention.py              # preview (read-only)
  python3 scripts/retention.py apply        # delete expired entries
  python3 scripts/retention.py configure    # set built-in retention settings
  python3 scripts/retention.py schedule     # weekly launchd job (macOS)

Machine-local settings (CodeGraph search roots) live in
~/Library/Application Support/agent-setup/retention.json.
"""
import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "shared" / "retention" / "policy.json"
LABEL = "com.agent-setup.retention"
SKIP_DIRS = {"node_modules", ".git", ".venv", "venv", "__pycache__", "dist", "build"}


def homes(home):
    home = Path(home)
    return {
        "codex_home": Path(os.environ.get("CODEX_HOME") or home / ".codex"),
        "hermes_home": Path(os.environ.get("HERMES_HOME") or home / ".hermes"),
        "claude_home": Path(os.environ.get("CLAUDE_CONFIG_DIR") or home / ".claude"),
    }


def state_dir(home):
    base = Path(home) / ("Library/Application Support" if sys.platform == "darwin" else ".local/state")
    return base / "agent-setup"


def local_config(home):
    path = state_dir(home) / "retention.json"
    return json.loads(path.read_text()) if path.is_file() else {}


def newest_mtime(path):
    """Age of an entry is its most recent change; a touched folder stays alive."""
    latest = path.lstat().st_mtime
    if path.is_dir() and not path.is_symlink():
        for current, dirs, files in os.walk(path, followlinks=False):
            for name in dirs + files:
                try:
                    latest = max(latest, (Path(current) / name).lstat().st_mtime)
                except OSError:
                    continue
    return latest


def size_of(path):
    if path.is_symlink() or path.is_file():
        return path.lstat().st_size
    total = 0
    for current, _, files in os.walk(path, followlinks=False):
        for name in files:
            try:
                total += (Path(current) / name).lstat().st_size
            except OSError:
                continue
    return total


def inside(path, root):
    try:
        return path.parent.resolve().is_relative_to(root.resolve())
    except OSError:
        return False


def entries(item, paths, home):
    select = item["select"]
    if select == "codegraph":
        found = []
        for raw in local_config(home).get("codegraph_roots", []):
            base = Path(os.path.expanduser(raw))
            if not base.is_dir():
                continue
            for current, dirs, _ in os.walk(base, followlinks=False):
                depth = len(Path(current).relative_to(base).parts)
                if ".codegraph" in dirs and not (Path(current) / ".codegraph").is_symlink():
                    found.append((Path(current) / ".codegraph", base))
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".") and depth < 5]
        return found
    root = Path(item["root"].format(**{k: str(v) for k, v in paths.items()}))
    if not root.is_dir() or root.is_symlink():
        return []
    if select == "files":
        return [(p, root) for p in root.glob(item["glob"]) if p.is_file() and not p.is_symlink()]
    if select == "entries":
        return [(p, root) for p in root.glob(item["glob"]) if not p.is_symlink() and p.name != ".DS_Store"]
    raise ValueError("unknown select: " + select)


def candidates(item, paths, home, now):
    found = []
    for path, root in entries(item, paths, home):
        if not inside(path, root):
            continue
        found.append((newest_mtime(path), path))
    found.sort(reverse=True)
    keep = item.get("keep_latest", 3)
    cutoff = now - item["days"] * 86400
    return [path for mtime, path in found[keep:] if mtime < cutoff], len(found)


def remove(path):
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def run_gam(home, apply):
    """Invoke the shared adapter with executor-neutral installation discovery.

    Local retention.json may set gam_python, gam_command, gam_config,
    gam_vault and gam_state. Codex tools.json is a compatibility fallback.
    """
    settings = local_config(home)
    python = settings.get("gam_python")
    command = settings.get("gam_command")
    if not python:
        uv = shutil.which("uv")
        if uv:
            found = subprocess.run([uv, "tool", "dir"], capture_output=True, text=True, timeout=30)
            if found.returncode == 0:
                candidate = Path(found.stdout.strip()) / "global-memory-mcp/bin/python"
                if candidate.is_file():
                    python = str(candidate)
    if not python:
        tools = state_dir(home).parent / "codex-setup/tools.json"
        if tools.is_file():
            record = json.loads(tools.read_text())
            python, command = record.get("python"), command or record.get("gam_mcp")
    if not python or not Path(python).is_file():
        return {"status": "skipped", "reason": "GAM Python unavailable; set gam_python in local retention.json"}
    script = ROOT / "shared/skills/core/gam-memory/scripts/gam_retention.py"
    args = [python, str(script), "--policy", str(POLICY)]
    for key, flag in (("gam_config", "--config"), ("gam_vault", "--vault"), ("gam_state", "--gam-state")):
        if settings.get(key):
            args += [flag, settings[key]]
    if command:
        args += ["--command", command]
    if apply:
        args += ["--apply"]
    done = subprocess.run(args, capture_output=True, text=True, cwd=script.parent, timeout=600)
    if done.returncode:
        return {"status": "failed", "exit_code": done.returncode, "reason": "GAM lifecycle adapter failed; inspect local stderr privately"}
    try:
        result = json.loads(done.stdout)
        failed = any(r.get("outcome") == "failed" for r in result.get("receipts", []))
        return dict(result, status="failed" if failed else "ok")
    except ValueError:
        return {"status": "failed", "reason": "GAM lifecycle adapter returned invalid JSON"}


def sweep(home, apply=False, policy=None, now=None, gam=True):
    policy = policy or json.loads(POLICY.read_text())
    now = now or time.time()
    paths = homes(home)
    report = {"apply": apply, "at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "items": {}}
    for item in policy["items"]:
        doomed, total = candidates(item, paths, home, now)
        size = sum(size_of(p) for p in doomed)
        row: dict = {"entries": total, "expired": len(doomed), "bytes": size}
        if apply:
            removed = 0
            for path in doomed:
                try:
                    remove(path)
                    removed += 1
                except OSError as error:
                    row.setdefault("errors", []).append(f"{path.name}: {error.strerror}")
            row["removed"] = removed
        report["items"][item["id"]] = row
    if gam and policy.get("gam", {}).get("temporary_expiry_archive"):
        report["gam"] = run_gam(home, apply)
    if apply:
        receipt = state_dir(home) / "retention" / "last-run.json"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


def configure(home, policy=None):
    policy = policy or json.loads(POLICY.read_text())
    paths = homes(home)
    result = {}
    for rule in policy["builtin"]:
        if rule["id"] == "claude-transcripts":
            settings = paths["claude_home"] / "settings.json"
            if not paths["claude_home"].is_dir():
                result[rule["id"]] = "skipped: Claude Code not installed"
                continue
            data = json.loads(settings.read_text()) if settings.is_file() else {}
            if data.get(rule["setting"]) == rule["value"]:
                result[rule["id"]] = "unchanged"
                continue
            if settings.is_file():
                shutil.copy2(settings, settings.with_name("settings.json.agent-setup-retention.bak"))
            data[rule["setting"]] = rule["value"]
            settings.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
            result[rule["id"]] = "set"
        elif rule["id"] == "hermes-sessions":
            hermes = shutil.which("hermes")
            if not hermes:
                result[rule["id"]] = "skipped: hermes CLI not found"
                continue
            values = {rule["setting"]: rule["value"], **rule.get("also", {})}
            for key, value in values.items():
                subprocess.run([hermes, "config", "set", key, json.dumps(value)], check=True,
                               capture_output=True, text=True)
            result[rule["id"]] = "set"
        else:
            result[rule["id"]] = "built-in"
    return result


def schedule(home, policy=None):
    if sys.platform != "darwin":
        raise SystemExit("schedule supports macOS launchd; use cron with `retention.py apply` elsewhere")
    policy = policy or json.loads(POLICY.read_text())
    when = policy["schedule"]
    logs = state_dir(home) / "retention"
    logs.mkdir(parents=True, exist_ok=True)
    plist = Path(home) / "Library/LaunchAgents" / (LABEL + ".plist")
    body = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>{LABEL}</string>
  <key>ProgramArguments</key>
  <array><string>{sys.executable}</string><string>{Path(__file__).resolve()}</string><string>apply</string></array>
  <key>StartCalendarInterval</key>
  <dict><key>Weekday</key><integer>{when['weekday']}</integer><key>Hour</key><integer>{when['hour']}</integer><key>Minute</key><integer>{when['minute']}</integer></dict>
  <key>StandardOutPath</key><string>{logs / 'launchd.log'}</string>
  <key>StandardErrorPath</key><string>{logs / 'launchd.log'}</string>
</dict>
</plist>
"""
    plist.parent.mkdir(parents=True, exist_ok=True)
    plist.write_text(body)
    domain = f"gui/{os.getuid()}"
    subprocess.run(["launchctl", "bootout", f"{domain}/{LABEL}"], capture_output=True)
    done = subprocess.run(["launchctl", "bootstrap", domain, str(plist)], capture_output=True, text=True)
    return {"plist": str(plist), "loaded": done.returncode == 0, "detail": done.stderr.strip()[:200]}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", nargs="?", default="plan", choices=("plan", "apply", "configure", "schedule"))
    parser.add_argument("--home", default=str(Path.home()))
    args = parser.parse_args()
    if args.action == "configure":
        out = configure(args.home)
    elif args.action == "schedule":
        out = schedule(args.home)
    else:
        out = sweep(args.home, apply=args.action == "apply")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
