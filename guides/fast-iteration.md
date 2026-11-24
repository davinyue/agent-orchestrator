# Fast Iteration

Choose this workflow when low latency matters more than full multi-agent isolation.

## Option 1: Keep the installed profile, limit delegation

Stay on `NeonXHigh-FlashHigh`, keep small edits root-only, and skip the `reviewer` subagent on low-risk exploratory changes. Spawn `explorer` or `tester` only when parallel inspection genuinely saves wall time.

## Option 2: Antigravity built-in Orchestrator mode

For fast single-conversation planning + execution without spinning up multiple subagent threads, switch the model selector to Antigravity's built-in **Orchestrator** mode:

- **Antigravity App**: select **Orchestrator** in the model selector and configure **Gemini 4 Neon** as the planner and **Gemini 4 Hydrogen** as the executor under **Settings > Models > Orchestrator Settings**.
- **Antigravity CLI**:

  ```sh
  agy --model "Orchestrator (Neon)"
  ```

Built-in Orchestrator hands off between planner and executor inside a single turn, reducing orchestration overhead for medium-sized tasks where independent subagent contexts are unnecessary.
