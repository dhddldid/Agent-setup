---
name: dag-ulw-notes
description: "Use for multi-part jobs and dag-ulw runs. Split first."
metadata:
  hermes:
    related_skills: [dag-ulw]
---

# dag-ulw notes

Companion to `dag-ulw` (OMH-managed, not patchable). Load `dag-ulw` first; this adds the start rules that keep work from running one agent at a time, and the define-time rules that cost a full re-send of the node list when missed.

## Starting: split before the first dispatch

The user loses hours when parts that could run together are run one by one, and treats it as a basic failure.

1. Load `dag-ulw` yourself on any request with several parts (build stages, several features, research + build + verify), whatever language it is in. OMH's turn hint matches dag-ulw only on English/Russian cue words, so Korean requests ("개발해", "진행해", "인프라 만들어줘") arrive with no hint or a wrong one; do not wait for one.
2. A decided stage order (0 → 1 → 2 → 3) is the order results are consumed, not the order code must be written. Fix the interface a later part needs from an earlier one (API shape, table names, auth stub), then build both together against stand-ins; only parts that need a real result to decide their design wait.
3. Dispatch every ready node in ONE `delegate_task` call. A spawn with a single task while other parts are pending needs a one-line reason in the status message (shared write scope, real data dependency); "keeping it safe" is not one.
4. dag-ulw starts without plan approval. Ask only for spend, scope growth or irreversible steps, never for permission to parallelize work already approved.
5. Give each parallel coding node its own worktree and a disjoint slice of shared numbered resources (migration numbers, ports) so merges do not collide.

## Before calling `omh_dag action=define`

1. Node ids: lowercase letters, digits and hyphens only (`w39-db`). An underscore is refused as `invalid_node_id`.
2. `goal`: one short sentence. A long criteria line is refused as `invalid_goal` even when it has no line break; put detailed criteria in node VERIFY lines instead.
3. Write scopes: every pair of nodes writing the same path needs a DIRECT `depends_on` edge. A transitive chain (a -> b -> c) still fails `write_scope_overlap` for a and c, so list all earlier same-scope producers in a later node's `depends_on`.
4. Shared context: write the context every node needs (repo path, project rules to read, check commands, no-deploy/no-commit boundary, design doc path) to one scratch file and end each prompt with `CONTEXT: read <path> first`. The define payload stays small, so a refused define is cheap to re-send.
5. Give every node all five markers (TASK, DELIVERABLE, SCOPE, VERIFY, STOP WHEN); a missing DELIVERABLE only lints, but the lint is noise in every later status.
6. A single-repo backend-then-frontend change is legitimately serial; the `serial_graph` lint is advice, so accept it when nodes share one write scope.
7. Each node prompt (repair nodes included) is capped at 3000 characters (`invalid_prompt`). Put long rulings or finding lists in a scratch file and reference it from the prompt.

## While the run is going

- Scope added by the user mid-run: `delegate_task action=steer` the running child with the exact addition (and update the design doc first), then append a short "Parent additions" paragraph to the `context` of every later node you dispatch; the saved node prompts are not re-sent automatically.
- Open items a child reports ("not in scope", "left for services") need a parent ruling in the NEXT node's context; unresolved they resurface as review blockers.
- Children in one shared worktree: forbid `git stash` and any command that moves other files; one child's stash/pop briefly removes every other node's tracked changes.
- Review found defects: settle the review node `failed`, then `repair` with a fix node + re-review node. Only two repair cycles exist per node, so the fix node must cover concurrency classes too (lock order across all paths that change the same rows, re-check after locking), not only the reproduced cases; a narrow fix tends to fail the re-review on a sibling race.
- Speed: tell build nodes to run the targeted test files while iterating and the full suite once before handoff; the separate verify node runs the full suite again. Full-suite runs per node dominate wall time when tests hit a remote database, so give nodes a local database + parallel runner command in the shared context file and keep the remote-DB run for verify only.
- Re-review leaves only a narrow finding and the repair budget is spent: fix it in the parent with a regression test proven to fail without the fix, settle the re-review node `accepted` with that reason, and let verify run.
- Independent features that share no files ship sooner as separate runs or separate deploys than as one batch waiting on the slowest feature.
