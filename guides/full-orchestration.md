# Neon XHigh + Flash High Orchestration

Choose the default `NeonXHigh-FlashHigh` profile when you want **Gemini 4 Neon (Extra High)** to plan, orchestrate, integrate, and independently review while Flash-tier execution roles handle codebase exploration, bounded coding, testing, and research.

## Topology

```text
Gemini 4 Neon (Extra High) root (`gemini-4-neon-xhigh`)
├── explorer   (model: flash / target: gemini-3.8-flash-high, read-only)
├── worker     (model: flash / target: gemini-3.8-flash-high, workspace-write)
├── tester     (model: flash / target: gemini-3.8-flash-high, workspace-write)
├── researcher (model: flash / target: gemini-3.8-flash-high, read-only + web)
└── reviewer   (model: inherit -> gemini-4-neon-xhigh, read-only)
```

## Project-scoped installation

Run `./setup.sh` (or `setup.ps1`) and pick profile `1` (`NeonXHigh-FlashHigh`), or manually copy:

- `profiles/NeonXHigh-FlashHigh/agents/` -> `<target-repo>/.agents/`
- `AGENTS.md` -> `<target-repo>/AGENTS.md` (append if the file already exists)

Antigravity discovers `.agents/agents/*.md`, `.agents/skills/agy-orchestrator/SKILL.md`, and `AGENTS.md` automatically in Antigravity App, Antigravity CLI, and Antigravity IDE.

## Configuring the root model

### Antigravity App / IDE

Select **Gemini 4 Neon** in the model selector and set thinking level to **Extra** (`Gemini 4 Neon (XHigh)`).

### Antigravity CLI

Start a session directly:

```sh
agy --model gemini-4-neon-xhigh
```

Or merge `profiles/NeonXHigh-FlashHigh/cli/settings.json` into `~/.gemini/antigravity-cli/settings.json`:

```json
{
  "$schema": "https://antigravity.google/schemas/v1/settings.json",
  "model": "Gemini 4 Neon (XHigh)",
  "agentMode": "auto",
  "toolPermission": "proceed-in-sandbox",
  "enableTerminalSandbox": true
}
```

## Exact model pinning with `/swarm`

In Antigravity's `invoke_subagent` tool and `.agents/agents/*.md` YAML frontmatter, `model` accepts only tier values (`inherit`, `flash_lite`, `flash`, `pro`). As a result:

- `reviewer` (`model: inherit`) runs the exact root model (`gemini-4-neon-xhigh`).
- `explorer`, `worker`, `tester`, and `researcher` (`model: flash`) run Antigravity's Flash subagent tier.

When you explicitly want exact per-worker model pinning (`gemini-3.8-flash-high` for execution roles and `gemini-4-neon-xhigh` for coordinator & reviewer), invoke `/swarm` and instruct the coordinator to verify live IDs via `swarm{action:"models"}`, pin execution workers to `Gemini 3.8 Flash (High)` (`gemini-3.8-flash-high`), and leave `@reviewer` on the coordinator's `Gemini 4 Neon (XHigh)` model.

> **Lifecycle note**: Antigravity lists **Gemini 3.8 Flash** as scheduled for removal on **November 30, 2026**. After removal, pin `/swarm` execution workers to **Gemini 4 Hydrogen (High)** (`gemini-4-hydrogen-high`).

For a 2-subagent concurrency cap and global `~/.gemini/config/` installation, see [low-concurrency.md](low-concurrency.md).
