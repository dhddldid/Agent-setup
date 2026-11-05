---
name: gam-memory
description: Use when retaining project knowledge. Apply GAM lifecycle.
---

# Project memory governed by OMH

Run this procedure inside the selected OMH workflow. Use GAM first for project
knowledge across Hermes, Claude Code and Codex. Keep current contracts and source
evidence in project documents; keep reusable procedures in skills. Hermes OMH
memory retains Hermes-operation lessons. Preserve both stores and their settings.
Policy: `shared/retention/policy.json` in Agent-setup; user guide:
`docs/memory-lifecycle.md`. The scripts beside this skill implement portable
preflight, deadlines, recall gates and report-first retention.

## 1. Resolve the authorized project

- Call `memory_projects(action="detect", payload={working_directory})` with the
  absolute working directory. The payload key is `working_directory`.
- If detection returns null, list registered projects and inspect roots before
  adding one with `action="add", request_id, payload={name, roots:[git_root]}`.
  Use its registered name/ID as `project`; put paths in `working_directory`.
- Confine reads/writes to the authorized project and account. Treat cross-project
  results as an isolation failure. GAM global/organization labels require their
  own account-boundary enforcement; retain personal/company knowledge in project scope.
- On rename/move update the same registry ID: `action="update", request_id,
  payload={id, changes:{name, roots, aliases:[old_name]}}`. Read registry roots and
  detect at the new directory to verify. Top-level roots/aliases may be ignored.

## 2. Recall eligible evidence

At project start search with `project`, `working_directory`, `scopes=["project"]`,
`statuses=["active"]`, `cross_project=false`, and all include_candidates,
include_rejected, include_archived, include_superseded flags explicitly false.
Page with cursor before claiming complete coverage. Check each exact target with
`memory_get`; compare its source and source digest with current evidence.

Use `scripts/lifecycle.py:classify` and `recall` on fetched records before using
content. Expired, stale, unsafe, unknown-source, pending, rejected and superseded
records stay outside ordinary evidence. Inspect stale records separately for
revalidation. A subject's newest value suppresses older values even when the newest
expires. Reference attention requires query overlap; archived attention needs an
explicit inspection request. Track delivered IDs+versions per session to suppress
same-revision repeats; keep usage counts only from observed delivery.
`memory_context(task, project, working_directory, cross_project=false,
token_budget=3000)` supplies bounded native packing; postvalidate every source or
build a strict bounded prefix from validated search/get records. GAM hybrid ranking
is approximate; the native OMH tokenizer, scoring, attention and usage ladder have
no parity guarantee. Store attention tier separately from GAM lifecycle status.

## 3. Capture at the right time

Save a lasting user-stated fact, decision or correction in the same turn before
other tools. Save verified solutions once supporting evidence exists. One fact per
call, 1–2 declarative sentences, <=500 characters; use absolute dates, a bounded
source_ref <=160 characters, 2–5 user-language topic tags and <=8 total tags.
Choose observations over commands. Keep source documents canonical. A reference
request stores the canonical document/section pointer with `type=reference` and
explicitly marked unknowns.

Exclude raw conversations/logs, pasted or quoted instructions, credentials,
opaque secret-like values, guesses, progress, task completion and temporary TODOs.
Review summary, title, body, tags, source and metadata before persistence. Re-author
redacted/unsafe payloads from safe evidence before any API call. Store only the
sanitized summary, source pointer, dates and lifecycle contract; keep raw source
outside GAM. `scripts/admission.py:admission` supplies bounded deterministic
preflight and reason codes; agent review covers semantic safety and eligibility.
It is a portable screen with a documented OMH classifier-parity gap.

Search same-project eligible records first. Compare NFC/lowercase/collapsed-space
summaries (`duplicate_key`), skipping exact live duplicates with their verified ID.
Expired records permit refresh. Similar wording and subject matches prompt a
semantic choice: independent fact, duplicate, or changed value. Near matches alone
never justify discarding a correction. Set `force=false` explicitly; direct tool
calls have best-effort concurrency. Serialize cooperating writers by project and
subject, recheck inside their shared lock; backend atomic capture remains a gap.

## 4. Assign lifecycle before remember

Semantic types map to GAM V1 types:

| Semantic | GAM | standard TTL / review |
|---|---|---|
| fact | fact; preference/reference/entity/project retain native meaning | none / 90d |
| decision | decision | none / 90d |
| lesson | solution | none / 90d |
| procedure | convention | none / 90d |
| episode | session_summary | 30d / none |

Model captures default `fact` + `durable`; CLI/admission imports explicitly choose
`standard`. Durable has no default TTL/review. Explicit review cadence survives
durable classification. Volatile defaults to 7d, accepts integer 1–7d, and permits
only a TTL override. Use `derive` with timezone-qualified capture timestamps;
absolute expiry and TTL are mutually exclusive, as are absolute review and review
days. Durable refuses TTL. Preserve computed dates through approval/tag/body edits;
recompute class changes with provenance and retain explicit review cadence.

Persist the full contract under `metadata.lifecycle` only after verifying metadata
roundtrip, or in this portable body section (fenced JSON):

    ## GAM lifecycle
    ```json
    {"policy_version":2,"semantic_type":"fact","retention_class":"durable","captured_at":"2026-11-05T00:00:00+00:00","confirmed_at":"2026-11-05T00:00:00+00:00","expires_at":null,"review_due_at":null,"cadence_source":"default","safety_status":"safe"}
    ```

Include source_ref/digest, admission_mode, subject, attention_tier and derived_from
when applicable. Compact `omh-type:*`, `retention-class:*`, `subject:*` tags aid
discovery. `temporary` and `expires:YYYY-MM-DD` project exact expiry into legacy
indexes; UTC `now >= expires_at` controls eligibility. Legacy unclassified records
enter classification review, preserving timestamps. Expiry warnings use
min(14d, max(floor(lifespan_days/2),1d)); expiry warnings precede review warnings.

Explicitly retained unresolved project decisions use `resolution=open`, open_since,
review_due_at (default90d), next_ask_at (14d) and, for non-durable records,
open_expires_at (365d). Keep them in a separate open-question pack. Reaching the
ceiling schedules review; retain open status until a sourced resolution. Durable
open records have no ceiling. Ordinary TODO/progress belongs in work tracking.

## 5. Candidate, conditional approval, verified recall

`shared/rules/common.md` authorizes the auto-safe branch. Respect memory_mode:
`off` skips capture, `review-first` keeps candidates pending, `auto-safe` approves
only safe AND nonduplicate AND non-derived AND force_review=false AND
absolute-time-anchored candidates. Unknown safety requires review. Relative dates
require a known absolute anchor before retry. A derived aggregate always requires
review. Preserve review reason precedence: safety, relative time, duplicate,
derived, policy. Pending duplicate candidates remain pending.

1. Call `memory_remember(request_id, title, content, type, scope="project",
   project, working_directory, source_kind, source_ref, tags, force=false)`.
   Send all content fields explicitly; this creates a candidate.
2. `memory_get(id)`; verify persisted summary, scope, source, dates, sanitized
   metadata, status and exact returned version. Re-evaluate the approval gates.
3. For the eligible branch call `memory_approve(id, request_id,
   expected_updated_at=version)`. Preserve the returned version string byte for
   byte, including `+00:00` versus `Z`. On conflict read again and re-review;
   repeated blind retries can trigger server backoff. Apply the same version
   guard to `memory_update` and `memory_reject`.
4. Read the exact ID again; verify active status and project-scoped search with
   exact_project_match. Reapply lifecycle/source gates. Report connection,
   candidate creation, approval and successful recall as separate observations.
   Receipts contain IDs, versions, digests and reasons; raw content stays private.

## 6. Curation, correction and rejected evidence

- Review consolidation every5 user turns. Session close/shutdown/recovery use
  the same >=5 threshold. Compaction independently triggers review. Duplicates,
  expired/expiring records and measured native-file headroom independently trigger
  it too. For a known native cap, floor=min(300,max(cap,0)*300//2200), checked per
  file; GAM retrieval storage has no corresponding fixed headroom cap.
- Persist private per-executor/profile/project/session counters, pending review
  and last standing reason strings. Suppress unchanged standing reasons; recurring
  interval/compaction events can recur. A prepared review brief and actual curation
  are separate outcomes. A new remember alone counts as capture. Record a reviewed
  no-change outcome honestly. `consolidation_reasons` computes checkpoint reasons;
  host turn/session/compaction hook integration remains unverified on all executors.
- At resume/compaction compare canonical decisions and capture new lasting
  user-stated constraints only. Leave unsourced original entries intact.
- Changed decisions: approve/read back the replacement, re-read the observed old
  revision, call `memory_supersede(old_id, replacement_id, request_id, reason)`,
  read both exact IDs and verify reciprocal links/history and eligible new recall.
  derived_from expresses lineage; use supersede for replacement. GAM supersede
  lacks an old-version CAS argument; recheck and disclose the residual race.
- Rejected candidates: `memory_reject(id, request_id, reason,
  expected_updated_at=version)` and exact-ID readback. When the user reopens a
  proposal or requests curation, search only `statuses=["rejected"]`,
  include_rejected=true, project scope, cross_project=false; requested tags must
  be a subset. Keep decision-only reviewed, safe, unexpired, fresh, unsuperseded
  negative evidence separate from ordinary context. Default6/max20. OMH ordering
  uses query overlap, reviewed_at desc, ID asc; native GAM order remains approximate.
  include_stale supplies metadata only; stale negative evidence stays excluded.
- Native memory transfer: retain identity/address/language/voice in native user
  memory. For a unique whole project entry <=240 chars, first create/approve/read
  back its exact intact durable GAM copy; only then remove that exact native entry
  through the executor's memory tool. Pending/rejected/redacted/truncated copies
  preserve the original. Universal facts need an equivalent authorized global
  recall store before transfer. Record IDs/hashes/lengths only in transfer receipts.
- Run report-first retention through Agent-setup `scripts/retention.py` or this
  skill's `scripts/gam_retention.py --policy <shared policy>`. Apply only authorized
  expiry rows. Archive protection is a local overlay: expired protected entries
  still leave ordinary recall and appear in reports. Stale/source-unknown/open
  entries receive review. Live retirement requires a fresh observed target and
  explicit reason/authorization. Use memory_archive(hard_delete=false), verify
  exact archived status and exclusion from active retrieval. The archive API lacks
  version CAS/tombstone transaction support; keep this gap visible. Restore through
  a newly reviewed replacement linked to the archive, preserving history.
