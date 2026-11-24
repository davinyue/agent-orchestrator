# Antigravity (AGY) Orchestrator — Gemini 4 Neon (XHigh) + Gemini 4 Hydrogen (High)

Install an Antigravity (AGY) multi-agent orchestration profile with **Gemini 4 Neon (Extra High)** as the root orchestrator and independent reviewer, and **Gemini 4 Hydrogen (High)** / Flash-tier execution subagents (`explorer`, `worker`, `tester`, `researcher`).

Works across **Antigravity App**, **Antigravity CLI (`agy`)**, **Antigravity IDE**, and Antigravity IDE extensions.

## Orchestration topology

```text
          Gemini 4 Neon (Extra High)
            `gemini-4-neon-xhigh`
              root / orchestrator
                       |
       +---------------+---------------+
       |               |               |
    explorer         worker        researcher
  Flash / G4       Flash / G4      Flash / G4
  Hydrogen High    Hydrogen High   Hydrogen High
       |               |
       +-------+-------+
               |
            tester
    Flash / G4 Hydrogen High
               |
           reviewer
   Gemini 4 Neon (Extra High)
     `gemini-4-neon-xhigh`
               |
               v
            root agent
       integrate + verify
```

### Model mapping across Antigravity surfaces

Antigravity supports two multi-agent delegation mechanisms with different model granularity:

1. **Standard Subagents (`invoke_subagent` + `.agents/agents/*.md`, default)**:
   - Antigravity's custom subagent frontmatter and `invoke_subagent` tool accept **model tiers** (`inherit`, `flash_lite`, `flash`, `pro`) rather than arbitrary exact model+effort IDs.
   - Start the root session on **Gemini 4 Neon (Extra / XHigh)** (`gemini-4-neon-xhigh`).
   - `reviewer.md` sets `model: inherit`, so it runs on `gemini-4-neon-xhigh`.
   - `explorer.md`, `worker.md`, `tester.md`, and `researcher.md` set `model: flash`, mapping to Antigravity's Flash subagent tier.
2. **Exact Model Pinning (`/swarm`)**:
   - When you explicitly start a swarm with `/swarm`, `swarm{action:"add", model:...}` accepts exact model identifiers verified via `swarm{action:"models"}`.
   - Keep coordinator and `@reviewer` on `gemini-4-neon-xhigh` (`Gemini 4 Neon (XHigh)`), and pin `@explorer`, `@worker`, `@tester`, and `@researcher` to `gemini-4-hydrogen-high` (`Gemini 4 Hydrogen (High)`).

## Setup

1. Clone this repository and switch to the `agy` branch:

   ```sh
   git clone -b agy <repo-url>
   cd agent-orchestrator
   ```

2. Run the installer for your platform:

   macOS/Linux:

   ```sh
   ./setup.sh
   ```

   Windows PowerShell:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\setup.ps1
   ```

   PowerShell 7:

   ```powershell
   pwsh -File .\setup.ps1
   ```

3. When prompted, enter an **existing target repository other than this one**, choose a profile by number or name (Enter selects `NeonXHigh-HydrogenHigh`), and confirm which components to install:

   ```text
   Target repository path: ../my-project
   Select Profile [1-2] (default 1): 1
   ```

The installer copies the selected Antigravity customizations into `.agents/` and installs or appends workspace rules to `AGENTS.md`. Existing `.agents/` files are updated only after confirmation; existing `AGENTS.md` content is preserved.

### Installed target project

```text
my-project/
├── .agents/
│   ├── agents/
│   │   ├── explorer.md
│   │   ├── researcher.md
│   │   ├── reviewer.md
│   │   ├── tester.md
│   │   └── worker.md
│   └── skills/
│       └── agy-orchestrator/
│           └── SKILL.md
└── AGENTS.md
```

### Selecting the root model (`Gemini 4 Neon Extra High`)

- **Antigravity App / IDE**: choose **Gemini 4 Neon** in the model selector and set the thinking level to **Extra** (`Gemini 4 Neon (XHigh)`).
- **Antigravity CLI**: launch with `--model gemini-4-neon-xhigh` (or run `/model` + `/effort xhigh` inside the TUI):

  ```sh
  cd ../my-project
  agy --model gemini-4-neon-xhigh
  ```

  To make this your default CLI configuration, merge `profiles/NeonXHigh-HydrogenHigh/cli/settings.json` into `~/.gemini/antigravity-cli/settings.json` (do not blindly overwrite existing keys).

## How to use the skill

For complex tasks, Antigravity automatically discovers `.agents/skills/agy-orchestrator/SKILL.md` and `.agents/agents/*.md`, or you can invoke the skill explicitly with a slash command:

```text
/agy-orchestrator
Implement the invoice export endpoint. Use explorer to map the path,
worker to implement it, and tester and reviewer to verify it.
```

## Profiles

| Choice | Profile | Root | Execution roles (`explorer`, `worker`, `tester`, `researcher`) | Reviewer | Concurrent subagents |
|---|---|---|---|---|---:|
| 1 (default) | `NeonXHigh-HydrogenHigh` | `gemini-4-neon-xhigh` | `gemini-4-hydrogen-high` (`model: flash` in subagents; exact in `/swarm`) | `gemini-4-neon-xhigh` (`model: inherit`) | 4 |
| 2 | `NeonXHigh-HydrogenHigh-max-2-subagents` | `gemini-4-neon-xhigh` | `gemini-4-hydrogen-high` (`model: flash` in subagents; exact in `/swarm`) | `gemini-4-neon-xhigh` (`model: inherit`) | 2 |

For personal/global installation across all repositories, copy `profiles/<profile>/agents/agents/*.md` into `~/.gemini/config/agents/`, copy `profiles/<profile>/agents/skills/agy-orchestrator/` into `~/.gemini/config/skills/agy-orchestrator/`, and append `AGENTS.md` to `~/.gemini/config/AGENTS.md`.

## Key directory structure

```text
.
├── profiles/
│   ├── NeonXHigh-HydrogenHigh/
│   │   ├── agents/
│   │   │   ├── agents/*.md
│   │   │   └── skills/agy-orchestrator/SKILL.md
│   │   └── cli/settings.json
│   └── NeonXHigh-HydrogenHigh-max-2-subagents/
│       ├── agents/
│       │   ├── agents/*.md
│       │   └── skills/agy-orchestrator/SKILL.md
│       └── cli/settings.json
├── guides/
├── scripts/
│   └── token_usage.py
├── tests/
│   ├── test_profiles.py
│   └── test_token_usage.py
├── AGENTS.md
├── setup.sh
├── setup.ps1
├── README.md
└── LICENSE
```

## Guides

- [Neon XHigh + Hydrogen High orchestration and manual setup](guides/full-orchestration.md)
- [Low-concurrency profile and global `~/.gemini/config/` setup](guides/low-concurrency.md)
- [Complex repository work (worktrees, `/plan`, `/swarm`, `/boost`)](guides/complex-repo-work.md)
- [Fast iteration](guides/fast-iteration.md) and [routine coding](guides/routine-coding.md)
- [Token usage and measurement](guides/token-usage.md)

## License

Licensed under the [Apache License 2.0](LICENSE).
