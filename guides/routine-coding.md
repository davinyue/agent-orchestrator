# Routine Coding

Choose this workflow for predictable, localized tasks (single-file bug fixes, boilerplate updates, dependency bumps, simple tests) where lower quota usage and faster turnaround are preferred.

## Recommended approach

1. Do **not** invoke `/agy-orchestrator` for trivial single-file edits — the skill's delegation gate already keeps genuinely small changes root-only.
2. Switch the session model directly to a fast model when you do not need `Gemini 4 Neon (Extra High)` reasoning:
   - **Antigravity CLI**:

     ```sh
     agy --model gemini-4-hydrogen-high
     ```

   - **Antigravity App / IDE**: select **Gemini 4 Hydrogen** with thinking level **High**.

Switch back to **Gemini 4 Neon (Extra / XHigh)** (`agy --model gemini-4-neon-xhigh`) when starting multi-file architecture work or independent code reviews.
