#!/usr/bin/env python3
"""3일 주기 병렬 점검 설치기. 기본 dry-run, --apply로 복사·등록한다.

Discord 정리 작업과 같은 Hermes --no-agent cron을 사용한다.
Hermes가 Python 스크립트를 직접 실행하고 빈 stdout의 알림을 생략하므로
LLM 호출 비용은 0이다. 72시간 간격은 월 경계에서도 3일 주기를 유지한다.
예약·실행·전달 상태는 hermes cron list / runs에서 확인한다.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
NAME = "parallel-gap-check"
SCRIPT = "parallel-gap-check.py"


def wrapper(root, home, python):
    return f'''#!/usr/bin/env python3
"""LLM 비용 0: 발견이 있는 점검만 stdout으로 전달한다."""
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path({str(root)!r})
HOME = Path({str(home)!r})
PYTHON = {str(python)!r}

def main():
    os.environ['HERMES_HOME'] = str(HOME)
    report_dir = HOME / 'reports' / 'parallel-gaps'
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    failed = False
    for command, extra in [('history', ['--days', '3']), ('routing', [])]:
        result = subprocess.run([PYTHON, str(ROOT / 'scripts/check_parallel_gaps.py'),
                                 command, *extra, '--quiet-clean', '--report-file',
                                 str(report_dir / (stamp + '-' + command + '.md'))],
                                capture_output=True, text=True, timeout=240)
        if result.stdout.strip():
            print(result.stdout, end='')
        if result.returncode not in (0, 1):
            print(command + ' 점검 오류: ' + result.stderr.strip(), file=sys.stderr)
            failed = True
    return 2 if failed else 0

if __name__ == '__main__':
    sys.exit(main())
'''


def plan(root, home, python, deliver):
    command = ["hermes", "cron", "create", "every 72h", "--name", NAME,
               "--script", SCRIPT, "--no-agent", "--interpreter", str(python),
               "--workdir", str(root), "--catch-up", "off", "--deliver", deliver,
               "--failure-deliver", "local"]
    return {"mode": "dry-run", "schedule": "every 72h", "no_agent": True,
            "llm_cost": 0, "script": str(home / "scripts" / SCRIPT),
            "report_dir": str(home / "reports/parallel-gaps"), "deliver": deliver,
            "silence": "발견 0건이면 stdout 생략", "command": command}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--home", type=Path, default=Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")))
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--deliver", default="local", help="알림 대상. 기본 local은 cron 실행 기록에 저장")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    home, python = args.home.expanduser().resolve(), args.python.expanduser().absolute()
    result = plan(ROOT, home, python, args.deliver)
    if args.apply:
        # 같은 이름의 작업을 중복 등록하지 않고 기존 설정의 검토를 요청한다.
        jobs_path = home / "cron/jobs.json"
        if jobs_path.exists():
            data = json.loads(jobs_path.read_text())
            jobs = data if isinstance(data, list) else data.get("jobs", [])
            if any(job.get("name") == NAME for job in jobs):
                parser.error("parallel-gap-check가 이미 등록되어 있습니다. hermes cron list로 확인하세요")
        target = Path(result["script"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(wrapper(ROOT, home, python), encoding="utf-8")
        env = {**os.environ, "HERMES_HOME": str(home)}
        subprocess.run(result["command"], check=True, env=env)
        # 등록된 정확한 작업의 no-agent·주기·스크립트를 저장소에서 다시 읽는다.
        saved = json.loads(jobs_path.read_text())
        jobs = saved if isinstance(saved, list) else saved.get("jobs", [])
        found = [job for job in jobs if job.get("name") == NAME]
        if len(found) != 1 or not found[0].get("no_agent") or found[0].get("script") != SCRIPT:
            raise RuntimeError("cron 등록값 읽기 검증 실패")
        result["mode"] = "applied"
        result["job_id"] = found[0]["id"]
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['mode']}: 3일(72시간)마다 history --days 3 + routing")
        print("Hermes --no-agent cron · LLM 호출 비용 0 · 발견 0건이면 조용히 종료")
        print(f"스크립트: {result['script']}\n보고서: {result['report_dir']}")
        print(f"알림 대상: {args.deliver} (local: cron 실행 기록)")
        print("등록 명령: " + shlex.join(result["command"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
