## OMH workflow use

Before acting on a work request in any language, choose the overall workflow by task shape; make this choice yourself:
- Use `dag-ulw` for a multi-part job with ordered dependencies or parallel parts.
- Use `ulw-work` to implement an accepted plan across lanes.
- Use `ulw-loop` for a long goal requiring repeated research, build, and verification cycles.
- Use `ulw-plan` or `omh-plan` for an undecided or risky plan.
- Use `omh-code-review` for a review.
- Act directly on one small, bounded change.
Load the chosen workflow with `skill_view` and follow it. Before claiming completion, load and follow `omh-verification-gate`.

- Apply custom and project skills inside the chosen workflow for project rules, accounts, tools, and checks; have each node and lane load the relevant skills.
- When an OMH Route Hint or skill shortlist appears, load the hinted skill with `skill_view` before the first action; follow it or explain in one line why another workflow fits.
- Call `omh_delegate_route` immediately before every `delegate_task` and follow its routing result.
- Use `omh_todo` to record and update work with three or more steps.
- Use `omh_agent_board` during multi-agent runs and `omh_run_summary` at their close to report recorded time and tokens.
- Report prepared plans and handoffs separately from observed execution and verification results.
- Report to the owner in Korean.
