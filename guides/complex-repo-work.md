# Complex Repository Work

Use this workflow for cross-cutting architecture changes, tricky concurrency bugs, or multi-package refactors where high-confidence reasoning and strict file-ownership isolation matter more than raw speed.

## Recommended Antigravity setup

1. Start with the [NeonXHigh-HydrogenHigh profile](full-orchestration.md) (`Gemini 4 Neon (Extra High)` for root and reviewer).
2. Begin with `/plan` (or `/grill-me` when design choices are unsettled) so the root agent produces a verified plan before spawning implementation workers.
3. Isolate parallel writers with Antigravity workspaces:
   - Pass `Workspace="share"` (or `"branch"` for a fully isolated clone) in `invoke_subagent` when two or more `worker` subagents edit or build at the same time.
   - Keep read-only roles (`explorer`, `researcher`, `reviewer`) on `Workspace="inherit"`.
   - Always merge or cherry-pick a `share`/`branch` worker's changes before calling `manage_subagents(Action="kill")`, since killing deletes its isolated workspace.
4. For broad, cleanly separable tasks across many packages, explicitly invoke `/swarm` (exact model pinning: coordinator + `@reviewer` on `gemini-4-neon-xhigh`, workers on `gemini-4-hydrogen-high`).
5. For deep single-problem debugging (race conditions, subtle algorithmic bugs), consider Antigravity's built-in `/boost` command on paid plans.
6. For uniform fan-out across dozens of files (such as per-file audits or migrations), use `/run-workflow` with `type_name="reviewer", model="inherit"` and execution steps on `model="flash"`.
