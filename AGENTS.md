# Antigravity project instructions

For complex coding tasks, use the `agy-orchestrator` skill when its trigger conditions match.

The root agent (`Gemini 4 Neon (Extra High)`) owns architecture, decomposition, integration, and final verification.
Prefer specialized subagents (`explorer`, `worker`, `tester`, `researcher` on Flash / `Gemini 3.8 Flash (High)`, and `reviewer` on `Gemini 4 Neon (Extra High)`) via `invoke_subagent` for bounded exploration, implementation, testing, review, and technical research.

Do not delegate trivial work merely for parallelism.
Do not let multiple implementation agents edit the same files without explicit ownership boundaries or isolated `share`/`branch` workspaces.
User instructions always take precedence over this orchestration policy.
