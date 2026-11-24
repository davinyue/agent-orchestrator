# Low-Concurrency Profile and Global Setup

Choose `NeonXHigh-FlashHigh-max-2-subagents` when you want the same **Gemini 4 Neon (Extra High)** root/reviewer + **Gemini 3.8 Flash (High)** / Flash-tier execution split while capping concurrent subagents at **2** to control quota consumption and parallel context overhead.

## Project installation

Run `./setup.sh` (or `setup.ps1`) and select choice `2` (`NeonXHigh-FlashHigh-max-2-subagents`). The installer copies `profiles/NeonXHigh-FlashHigh-max-2-subagents/agents/` to `.agents/` and installs or appends `AGENTS.md`.

## Global installation (`~/.gemini/config/`)

To apply the orchestration agents and skill across every project on your workstation (shared by Antigravity App, Antigravity CLI, and Antigravity IDE):

```sh
mkdir -p ~/.gemini/config/agents ~/.gemini/config/skills
cp profiles/NeonXHigh-FlashHigh-max-2-subagents/agents/agents/*.md ~/.gemini/config/agents/
cp -R profiles/NeonXHigh-FlashHigh-max-2-subagents/agents/skills/agy-orchestrator ~/.gemini/config/skills/
```

Then append `AGENTS.md` into `~/.gemini/config/AGENTS.md` (preserving any existing global rules):

```sh
printf '\n\n' >> ~/.gemini/config/AGENTS.md
cat AGENTS.md >> ~/.gemini/config/AGENTS.md
```

Workspace-level `.agents/` files always take priority over global `~/.gemini/config/` definitions when a project overrides a specific agent or skill.

For Antigravity CLI defaults, merge `profiles/NeonXHigh-FlashHigh-max-2-subagents/cli/settings.json` into `~/.gemini/antigravity-cli/settings.json` rather than overwriting unrelated settings.

See [token-usage.md](token-usage.md) to measure how capping concurrency affects token usage on your own tasks.
