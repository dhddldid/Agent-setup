## OMH workflow skills

OMH (oh-my-hermes) workflow skills (`omh-*`, `ulw-*`) are installed. Before acting on a work request in any language, choose the overall workflow by task shape; make this choice yourself:
- Use `ulw-work` with lanes for a multi-part job with ordered dependencies or parallel parts. (`dag-ulw` needs the Hermes `omh_dag` runtime, so this executor runs that shape as `ulw-work` lanes.)
- Use `ulw-work` to implement an accepted plan across lanes.
- Use `ulw-loop` for a long goal requiring repeated research, build, and verification cycles.
- Use `ulw-plan` or `omh-plan` for an undecided or risky plan.
- Use `omh-code-review` for a review.
- Act directly on one small, bounded change, a general answer, or a one-shot lookup.
Load the chosen workflow skill and follow it. Before claiming completion, load and follow `omh-verification-gate`.

- Apply custom and project skills (GAM, CodeGraph, Aside, coding-*, project skills) inside the chosen workflow for project rules, accounts, tools, and checks; have each lane load the relevant skills. These skills run inside the workflow and leave the workflow choice in place. When a coding-* skill and an OMH skill fit the same job, follow the OMH procedure and also apply the coding-* reporting and verification criteria.
- OMH skills use Hermes tool names. Produce the same result with this executor's equivalents: `omh_todo` is the executor's task list, `omh_memory` is GAM (gam-memory), `omh_delegate_route` and `delegate_task` are delegation under the model routing below, `omh_jev_ask` is an independent review by a different model family, `omh_codegraph_summary` is CodeGraph, `omh_agent_board` and `omh_run_summary` are Markdown records in the working folder, and `omh_reviewed` and `omh_operation_artifact` are result files and verification records. Any other `omh_*` tool produces the same artifact with files and commands.
- Keep OMH records in `.omh/` of the target repository. Report prepared plans and handoffs separately from observed execution and verification results.
