#!/usr/bin/env bash
# Update Hermes and OMH to their latest stable releases and keep Agent-setup customizations.
#
#   bash hermes/scripts/update.sh            # update
#   bash hermes/scripts/update.sh --dry-run  # print every step and resolved value; change nothing
#   bash hermes/scripts/update.sh --check    # report versions and customization state only
#
# Stops before any change when Agent-setup has no Hermes core patch for the new tag.
set -euo pipefail

MODE=run
for arg in "$@"; do
  case "$arg" in
    --dry-run) MODE=dry-run ;;
    --check) MODE=check ;;
    -h|--help) sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) printf '알 수 없는 옵션: %s (--dry-run, --check)\n' "$arg" >&2; exit 64 ;;
  esac
done

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
AGENT_SETUP=$(cd "$SCRIPT_DIR/../.." && pwd -P)
HELPERS="$SCRIPT_DIR/update_helpers.py"
HERMES_HOME=${HERMES_HOME:-$HOME/.hermes}
OMH_HOME=${OMH_HOME:-$HOME/.omh}
OMH_REPO=${OMH_REPO:-rlaope/oh-my-hermes}
WORK="${TMPDIR:-/tmp}"
WORK="${WORK%/}/agent-setup-update-$(date +%Y%m%d-%H%M%S)"
TOTAL=15
STEP=0
STOP_NOTE=''
DOCTOR_FAILED=''
# Filled by `eval` of update_helpers.py output.
HERMES_INSTALLED='' HERMES_CHANNEL='' HERMES_CHECKOUT=''
OMH_REAL='' OMH_KIND='' OMH_ROOT='' OMH_GENERATION='' OMH_INSTALLED='' OMH_CHANNEL=''
LEGACY_VENV='' LEGACY_SAFE=0 LEGACY_REASONS=''

step() { STEP=$((STEP + 1)); printf '\n[%d/%d] %s\n' "$STEP" "$TOTAL" "$1"; }
info() { printf '  %s\n' "$*"; }
warn() { printf '  ⚠ %s\n' "$*"; }
die() { printf '\n중단: %s\n' "$*" >&2; exit 1; }
show_cmd() { printf '  $'; printf ' %q' "$@"; printf '\n'; }
# Print a command; run it only in update mode.
act() { show_cmd "$@"; if [[ $MODE == run ]]; then "$@"; fi; }
# In update mode stop; in dry-run record where the real run would stop and continue the plan.
stop_or_note() {
  if [[ $MODE == run ]]; then die "$1"; fi
  warn "실제 실행이면 여기서 멈춥니다: $1"
  STOP_NOTE="${STOP_NOTE:-$1}"
}

pick_python() {
  local candidate
  for candidate in python3.13 python3.14 python3.12 python3; do
    if command -v "$candidate" >/dev/null 2>&1 \
      && "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 12))' 2>/dev/null; then
      command -v "$candidate"; return 0
    fi
  done
  return 1
}

latest_stable() {  # owner/repo -> X.Y.Z from the releases/latest redirect
  local url
  url=$(curl -fsSI -o /dev/null -w '%{redirect_url}' "https://github.com/$1/releases/latest") \
    || die "$1 최신 릴리스를 확인하지 못했습니다 (네트워크 확인)"
  "$PY" "$HELPERS" version-from-url "$url" || die "$1 최신 정식 릴리스 주소를 해석하지 못했습니다: $url"
}

resolve_omh() { eval "$("$PY" "$HELPERS" omh-info --bin "$OMH_BIN")"; }
resolve_hermes() { eval "$(hermes --version 2>/dev/null | "$PY" "$HELPERS" hermes-info)"; }
autostashes() { git -C "$HERMES_CHECKOUT" stash list 2>/dev/null | grep -c 'hermes-update-autostash' || true; }

case $MODE in
  run) printf 'Hermes·OMH 최신 정식 릴리스 업데이트를 시작합니다.\n' ;;
  dry-run) printf '미리보기(--dry-run): 실행할 단계와 확인한 값만 보여주고 아무것도 바꾸지 않습니다.\n' ;;
  check) printf '상태 점검(--check): 버전과 사용자 지정 상태만 보고합니다.\n' ;;
esac

step '위치와 도구 확인'
if [[ $MODE == run && -n ${HERMES_AGENT:-} ]]; then
  die 'Hermes 안의 터미널에서는 실행할 수 없습니다(업데이트가 게이트웨이를 재시작해 이 명령도 끊깁니다). 터미널 앱에서 직접 실행하세요.'
fi
PY=$(pick_python) || die 'Python 3.12 이상이 필요합니다. brew install python@3.13 후 다시 실행하세요.'
command -v hermes >/dev/null 2>&1 || die 'PATH에서 hermes를 찾지 못했습니다.'
command -v curl >/dev/null 2>&1 || die 'curl이 필요합니다.'
OMH_BIN=$(command -v omh) || die 'PATH에서 omh를 찾지 못했습니다.'
resolve_hermes
[[ -n $HERMES_INSTALLED && -d $HERMES_CHECKOUT/.git ]] \
  || die "hermes --version에서 설치 위치를 읽지 못했습니다 (설치 위치: ${HERMES_CHECKOUT:-없음})."
resolve_omh
[[ -n $OMH_INSTALLED ]] || die "실행 중인 omh의 패키지 버전을 읽지 못했습니다: $OMH_REAL"
info "Agent-setup: $AGENT_SETUP"
info "Python: $PY"
info "HERMES_HOME: $HERMES_HOME · OMH_HOME: $OMH_HOME"
info "hermes: $(command -v hermes) → v$HERMES_INSTALLED ($HERMES_CHANNEL), 소스 $HERMES_CHECKOUT"
info "omh: $OMH_BIN → $OMH_REAL"
info "omh 설치: $OMH_KIND ${OMH_GENERATION:+($OMH_GENERATION)} · $OMH_CHANNEL $OMH_INSTALLED · 루트 ${OMH_ROOT:-알 수 없음}"

step '실행 중인 Hermes 확인'
BUSY=0
if pgrep -x Hermes >/dev/null 2>&1; then
  warn 'Hermes Desktop이 실행 중입니다. 진행 중인 작업이 끝난 뒤 ⌘Q로 종료하고 실행하는 편이 안전합니다.'
  BUSY=1
fi
RUNNING_JOBS=$(hermes cron list 2>/dev/null | grep -cE 'Execution: +(claimed|pending|running|delivering)' || true)
if [[ ${RUNNING_JOBS:-0} -gt 0 ]]; then
  warn "실행 중인 예약 작업 ${RUNNING_JOBS}개가 있습니다. 끝난 뒤 실행하세요 (hermes cron list)."
  BUSY=1
fi
if [[ $BUSY -eq 0 ]]; then info '실행 중인 Desktop·예약 작업 없음'; fi
if [[ $BUSY -eq 1 && $MODE == run && -t 0 ]]; then
  read -r -p '  그래도 계속하려면 Enter, 멈추려면 Ctrl-C: ' _
fi

step '최신 정식 릴리스 확인'
HERMES_REPO=$(git -C "$HERMES_CHECKOUT" remote get-url origin 2>/dev/null \
  | sed -E 's#^(https://github.com/|git@github.com:)##; s#\.git$##')
[[ $HERMES_REPO == */* ]] || HERMES_REPO=NousResearch/hermes-agent
HERMES_LATEST=$(latest_stable "$HERMES_REPO")
OMH_LATEST=$(latest_stable "$OMH_REPO")
info "Hermes: 설치 v$HERMES_INSTALLED → 최신 정식 v$HERMES_LATEST ($HERMES_REPO)"
info "OMH: 설치 $OMH_CHANNEL $OMH_INSTALLED → 최신 정식 $OMH_LATEST ($OMH_REPO)"
HERMES_CHECK=$(hermes update --check 2>&1 || true)
printf '%s\n' "$HERMES_CHECK" | sed 's/^/  │ /'
if ! grep -q 'Update channel: stable' <<<"$HERMES_CHECK"; then
  stop_or_note 'Hermes 업데이트 채널이 stable이 아닙니다. hermes update --set-channel stable 후 다시 실행하세요.'
fi
if [[ $HERMES_INSTALLED != "$HERMES_LATEST" ]] \
  && ! "$PY" "$HELPERS" patch-exists --target hermes-agent --tag "v$HERMES_LATEST"; then
  stop_or_note "Agent-setup에 Hermes v${HERMES_LATEST}용 수정 묶음(hermes/patches/hermes-agent/v$HERMES_LATEST.patch)이 없습니다. 아무것도 바꾸지 않았습니다. AI에게 \"Agent-setup 수정 묶음을 Hermes v${HERMES_LATEST}에 옮겨줘\"라고 요청한 뒤 다시 실행하세요."
fi

step '보관 중인 Hermes stash 확인'
STASH_BEFORE=$(autostashes)
if [[ $STASH_BEFORE -gt 0 ]]; then
  warn "이전 업데이트가 남긴 자동 stash ${STASH_BEFORE}개가 보관되어 있습니다. 이 스크립트는 지우지 않습니다."
  git -C "$HERMES_CHECKOUT" stash list | grep 'hermes-update-autostash' | sed 's/^/    /'
  info "내용 확인: git -C $HERMES_CHECKOUT stash show --stat 'stash@{N}'"
else
  info '보관된 자동 stash 없음'
fi

step '사용자 지정 상태 스냅샷'
mkdir -p "$WORK"
BEFORE="$WORK/before.json"
"$PY" "$HELPERS" snapshot --out "$BEFORE" --hermes-home "$HERMES_HOME" --omh-home "$OMH_HOME" \
  --hermes-checkout "$HERMES_CHECKOUT" --omh-bin "$OMH_REAL"
info "저장: $BEFORE"
"$PY" "$HELPERS" summary "$BEFORE" | sed 's/^/  /'

if [[ $MODE == check ]]; then
  printf '\n점검을 마쳤습니다. 아무것도 바꾸지 않았습니다.\n'
  exit 0
fi

step 'Hermes 업데이트 (백업 포함)'
if [[ $HERMES_INSTALLED == "$HERMES_LATEST" ]]; then
  info "이미 최신 정식 v${HERMES_LATEST}입니다. 건너뜁니다."
else
  info '설정·대화 백업을 만든 뒤 로컬 수정을 stash에 보관하고 새 버전 위에 자동으로 다시 적용합니다.'
  act hermes update --backup --yes \
    || die 'hermes update가 실패했습니다. 위 출력에서 실패 단계와 업데이트 전 백업 위치를 확인하세요.'
  if [[ $MODE == run ]]; then
    resolve_hermes
    STASH_AFTER=$(autostashes)
    if [[ $STASH_AFTER -gt $STASH_BEFORE ]]; then
      warn '로컬 수정 재적용 중 충돌이 나서 Hermes가 새 stash를 보관했습니다. 다음 단계의 패치 적용으로 복구합니다.'
    fi
    [[ $HERMES_INSTALLED == "$HERMES_LATEST" ]] \
      || die "Hermes가 v${HERMES_INSTALLED}입니다 (기대 v$HERMES_LATEST). hermes update --check로 확인하세요."
  fi
fi

step 'Hermes 로컬 수정 묶음 재적용'
show_cmd "$PY" "$AGENT_SETUP/hermes/scripts/apply_local_patches.py" --apply
if [[ $MODE == run ]]; then
  if PATCH_OUT=$("$PY" "$AGENT_SETUP/hermes/scripts/apply_local_patches.py" --apply); then
    printf '%s\n' "$PATCH_OUT" | sed 's/^/  │ /'
  else
    printf '%s\n' "$PATCH_OUT" | sed 's/^/  │ /'
    die "수정 묶음을 새 버전에 적용하지 못했습니다(no_patch 또는 conflict). Hermes v${HERMES_INSTALLED}는 설치되었고 로컬 수정은 git stash에 보관되어 있습니다. AI에게 \"Agent-setup 수정 묶음을 Hermes v${HERMES_INSTALLED}에 옮겨줘\"라고 요청한 뒤 이 명령을 다시 실행하세요."
  fi
else
  info "현재 v$HERMES_INSTALLED 상태(읽기 전용 보고):"
  "$PY" "$AGENT_SETUP/hermes/scripts/apply_local_patches.py" | sed 's/^/  │ /' || true
fi

step 'Hermes 호환 패치 재적용 (위임 effort 보존, GPT 자식 fallback 순서)'
for script in configure_delegation_reasoning.py configure_gpt_fallback.py; do
  show_cmd "$PY" "$AGENT_SETUP/hermes/scripts/$script" --source-root "$HERMES_CHECKOUT" --apply
  if [[ $MODE == run ]]; then
    "$PY" "$AGENT_SETUP/hermes/scripts/$script" --source-root "$HERMES_CHECKOUT" --apply | sed 's/^/  │ /' \
      || die "$script 적용에 실패했습니다. Hermes 원본 구조가 바뀌었을 수 있으니 AI에게 호환 패치 이식을 요청하세요."
  fi
done

step "OMH 업데이트 (정식 $OMH_LATEST)"
if [[ $OMH_CHANNEL == stable && $OMH_INSTALLED == "$OMH_LATEST" ]]; then
  info "이미 정식 ${OMH_LATEST}입니다. 건너뜁니다."
else
  info 'OMH는 OMH_VERSION 환경변수를 읽지 않으므로 --channel stable --version을 직접 넘깁니다.'
  act "$OMH_REAL" update --channel stable --version "$OMH_LATEST" --yes --language ko \
    || die 'omh update가 실패했습니다. Hermes 업데이트와 패치는 끝났습니다. 위 출력과 omh doctor를 확인하세요.'
  if [[ $MODE == run ]]; then
    resolve_omh
    [[ $OMH_CHANNEL == stable && $OMH_INSTALLED == "$OMH_LATEST" ]] \
      || die "OMH가 $OMH_CHANNEL ${OMH_INSTALLED}입니다 (기대 stable $OMH_LATEST). omh doctor로 확인하세요."
    info "omh: $OMH_BIN → $OMH_REAL ($OMH_CHANNEL $OMH_INSTALLED)"
  fi
fi

step 'Agent-setup 설정 다시 맞추기 (SOUL 블록, 한국어 트리거 팩, provider-usage 표시)'
show_cmd "$PY" "$AGENT_SETUP/hermes/scripts/install_global_rules.py" --apply
if [[ $MODE == run ]]; then
  if ! RULES_OUT=$("$PY" "$AGENT_SETUP/hermes/scripts/install_global_rules.py" --apply 2>&1); then
    printf '%s\n' "$RULES_OUT" | sed 's/^/  │ /'
    die "SOUL.md의 Agent-setup 관리 블록을 직접 고친 내용이 있어 덮어쓰지 않았습니다. 위 차이 파일을 AI에게 보여주고 템플릿에 반영할지 정한 뒤 다시 실행하세요. Hermes·OMH 업데이트는 끝났습니다."
  fi
  printf '%s\n' "$RULES_OUT" | sed 's/^/  │ /'
fi
act "$PY" "$AGENT_SETUP/hermes/scripts/install_omh_trigger_pack.py" --apply \
  || die "한국어 트리거 팩을 설치하지 못했습니다. $OMH_HOME/routing/trigger-packs/ko.json을 확인하세요."
act "$PY" "$AGENT_SETUP/hermes/scripts/configure_provider_usage.py" --apply \
  || die 'provider-usage 표시 수정을 적용하지 못했습니다. 플러그인 파일 변경 여부를 확인하세요.'

step '설치 상태 점검'
for doctor in "omh doctor --language ko" "hermes doctor"; do
  # shellcheck disable=SC2086
  if [[ $MODE == run ]]; then
    show_cmd $doctor
    $doctor || { DOCTOR_FAILED="$DOCTOR_FAILED ${doctor%% *}"; warn "${doctor}가 실패를 보고했습니다."; }
  else
    show_cmd $doctor
  fi
done

step '사용자 지정 유지 확인'
if [[ $MODE == run ]]; then
  AFTER="$WORK/after.json"
  "$PY" "$HELPERS" snapshot --out "$AFTER" --hermes-home "$HERMES_HOME" --omh-home "$OMH_HOME" \
    --hermes-checkout "$HERMES_CHECKOUT" --omh-bin "$OMH_REAL"
  "$PY" "$HELPERS" diff "$BEFORE" "$AFTER" | sed 's/^/  /'
  info "스냅샷: $BEFORE, $AFTER"
else
  info "업데이트 뒤 같은 항목을 다시 읽어 ${BEFORE}와 비교한 표(유지/변경/없어짐)를 출력합니다."
fi

step '게이트웨이 재시작과 상태'
act hermes gateway restart || warn '게이트웨이 재시작이 실패했습니다. 아래 상태 출력을 확인하세요.'
act hermes gateway status || true

step '이전 OMH venv 정리'
eval "$("$PY" "$HELPERS" legacy-check --omh-bin "$OMH_BIN" --expected-version "$OMH_LATEST")"
if [[ ! -d $LEGACY_VENV ]]; then
  info "정리할 이전 venv가 없습니다 (${LEGACY_VENV:-경로 없음})."
elif [[ $LEGACY_SAFE == 1 && $MODE == run && -z $DOCTOR_FAILED ]]; then
  TRASH="$HOME/.Trash/omh-legacy-venv-$(date +%Y%m%d-%H%M%S)"
  info "PATH의 omh는 generation 설치본을 쓰고 이 venv는 아무 명령도 쓰지 않습니다."
  act mv "$LEGACY_VENV" "$TRASH"
  info '휴지통으로 옮겼습니다. 앞으로 curl 설치기로 업데이트하면 이 venv가 다시 생기니 이 명령으로 업데이트하세요.'
else
  info "남겨 둡니다: $LEGACY_VENV"
  if [[ $MODE != run ]]; then
    info "실행 시 업데이트·점검이 성공하고 아래 조건이 모두 풀리면 휴지통으로 옮깁니다."
  elif [[ -n $DOCTOR_FAILED ]]; then
    info "이유: 점검 실패(${DOCTOR_FAILED# }) 뒤에는 이전 venv를 옮기지 않습니다."
  fi
  if [[ -n $LEGACY_REASONS ]]; then info "현재 판단: $LEGACY_REASONS"; fi
fi

step '최종 버전'
if [[ $MODE == run ]]; then
  hermes --version | sed 's/^/  /'
  "$OMH_BIN" --version | sed 's/^/  /'
  if [[ -n $DOCTOR_FAILED ]]; then
    printf '\n업데이트는 끝났지만 점검 실패가 있습니다:%s. 위 출력을 확인하세요.\n' "$DOCTOR_FAILED"
    exit 2
  fi
  printf '\n완료. Hermes Desktop을 다시 켜고 새 세션에서 OMH 도구가 불리는지 확인하세요.\n'
else
  info "Hermes v$HERMES_INSTALLED → v$HERMES_LATEST"
  info "OMH $OMH_CHANNEL $OMH_INSTALLED → stable $OMH_LATEST"
  if [[ -n $STOP_NOTE ]]; then
    printf '\n미리보기 결과: 실제 실행은 다음 이유로 멈춥니다.\n  %s\n' "$STOP_NOTE"
  else
    printf '\n미리보기 결과: 위 단계를 그대로 실행할 수 있습니다. 아무것도 바꾸지 않았습니다.\n'
  fi
fi
