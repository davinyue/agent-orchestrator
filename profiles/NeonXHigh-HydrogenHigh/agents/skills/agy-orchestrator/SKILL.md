---
name: agy-orchestrator
description: "Orchestrate complex Antigravity (AGY) coding work with Gemini 4 Neon (Extra High) as root orchestrator and reviewer and Gemini 4 Hydrogen (High) / Flash tier for exploration, implementation, testing, and research. Use for multi-file features, debugging across components, repo-wide changes, parallelizable workstreams, or when the user asks to delegate. Do not use for trivial edits or simple questions."
---

# Antigravity Orchestrator — Gemini 4 Neon (XHigh) + Gemini 4 Hydrogen (High)

The user's explicit instructions always take precedence over this skill.

## Topology and Model Policy

Target model assignment:
- **root** (orchestrator / planner / integrator): `gemini-4-neon-xhigh` (**Gemini 4 Neon**, `Extra` / `xhigh` reasoning)
- **reviewer**: `gemini-4-neon-xhigh` (**Gemini 4 Neon**, `Extra` / `xhigh` reasoning), in an independent read-only context
- **explorer, worker, tester, researcher**: target `gemini-4-hydrogen-high` (**Gemini 4 Hydrogen**, `High` reasoning)
- **concurrency limit**: keep at most **4** active subagents running concurrently

How Antigravity enforces models across its two orchestration paths:
1. **Standard Subagents (`invoke_subagent` + `.agents/agents/*.md`, default path)**:
   - Antigravity's subagent schema supports model tiers (`inherit`, `flash_lite`, `flash`, `pro`) rather than arbitrary exact model+effort IDs.
   - Ensure the root session is running **Gemini 4 Neon (Extra / XHigh)** (`gemini-4-neon-xhigh`).
   - Invoke `reviewer` with `TypeName="reviewer"` and `Model="inherit"` so it runs on `gemini-4-neon-xhigh`.
   - Invoke `explorer`, `worker`, `tester`, and `researcher` with their named `TypeName` and `Model="flash"` (matching `model: flash` in `.agents/agents/*.md`).
2. **Exact Model Pinning (`/swarm`, only when the user explicitly invokes `/swarm`)**:
   - Never start a swarm unprompted. Only use the `swarm` tool when the user explicitly invoked `/swarm` or a swarm is already active.
   - Run `swarm{action:"models"}` first to inspect live available model identifiers and display names.
   - Keep the coordinator and `@reviewer` on `gemini-4-neon-xhigh` (`Gemini 4 Neon (XHigh)` — omit `model` when coordinator already runs it).
   - Pin `@explorer`, `@worker`, `@tester`, and `@researcher` to `gemini-4-hydrogen-high` (`Gemini 4 Hydrogen (High)`).

Do not silently substitute the root agent for a required Flash execution subagent, and do not escalate an execution role to `inherit`/`pro` unless the user asks or the subagent reports a genuine reasoning blocker.

## Delegation Gate

Before doing substantive repository work, classify the task as either:
- **root-only**: genuinely small, localized edits or direct questions that do not benefit from independent exploration, implementation, testing, research, or review.
- **delegated**: at least one of the following holds:
  - spans multiple files, modules, services, or components
  - contains two or more independent workstreams
  - benefits from codebase exploration before implementation
  - requires cross-component debugging
  - requires verifying external or version-specific facts
  - benefits from an independent post-change review
  - user explicitly asks to delegate or use subagents

When a task qualifies as delegated, call `invoke_subagent` for real instead of simulating delegation. If `invoke_subagent` is unavailable or fails, report the failure explicitly rather than claiming delegation happened.

## Antigravity Delegation Mechanics

1. **Spawn with `invoke_subagent`**:
   - `TypeName`: `"explorer"`, `"worker"`, `"tester"`, `"researcher"`, or `"reviewer"`
   - `Role`: short descriptive title distinguishing parallel agents (e.g., `"API Route Explorer"`, `"Invoice Export Worker"`)
   - `Model`: `"flash"` for `explorer` / `worker` / `tester` / `researcher`; `"inherit"` for `reviewer`
   - `Workspace`:
     - `"inherit"` for read-only roles (`explorer`, `researcher`, `reviewer`), single-writer `worker`, and `tester`
     - `"share"` (preferred) or `"branch"` when multiple `worker` subagents edit or build concurrently so they cannot collide on the same working tree; land/merge changes before killing any `share`/`branch` subagent because `manage_subagents(Action="kill")` deletes its isolated workspace
   - `Prompt`: a complete bounded delegation contract (objective, scope, context, constraints, deliverable, acceptance criteria)
2. **Wait reactively (no polling)**:
   - Launch independent subagents in parallel in the same turn, then stop calling tools or continue independent root work. Antigravity wakes the root automatically when each subagent replies.
3. **Reuse idle subagents**:
   - To continue a subagent's work on the same scope, call `send_message(Recipient=<conversationId>, Message=...)` instead of spawning a duplicate subagent.
4. **High-fan-out pipelines (`run_workflow`)**:
   - When a task fans out uniformly across many files or modules, `run_workflow` may be used with `type_name="reviewer", model="inherit"` and execution agents on `model="flash"`.

## Role Selection

- `explorer` (`Model="flash"`, read-only): map files, symbols, call/data flows, tests, and config before edits.
- `worker` (`Model="flash"`, workspace-write): implement bounded changes inside explicit file ownership boundaries.
- `tester` (`Model="flash"`, workspace-write): run targeted tests, reproduce bugs, add requested tests, report exact commands and outputs.
- `researcher` (`Model="flash"`, read-only + web): verify version-specific APIs, framework docs, and dependency compatibility from primary sources.
- `reviewer` (`Model="inherit"`, read-only): perform independent post-change review on correctness, regressions, security, concurrency, data integrity, and missing tests.

## Workflow Discipline

- **Parallelize independent work**: spawn independent explorers and researchers together before waiting; serialize dependent phases (`explore -> decide architecture -> implement -> test -> review -> fix material findings -> final verification`).
- **Concurrency cap**: never keep more than **4** active subagents running simultaneously.
- **Root ownership**: root owns user intent, architecture, decomposition, conflict resolution, integration, final diff inspection, and final verification.
- **Cost and context discipline**: instruct subagents to return concise evidence summaries (file paths, symbols, commands, pass/fail output, risks) rather than dumping raw logs.
- **Escalation**: subagents must stop expanding scope and report back if they hit an architectural decision, breaking API/schema change, new dependency, security-sensitive choice, or ownership conflict.
- **Do not spawn every role mechanically**: use only the roles that materially improve quality or turnaround.

## Completion Gate and Final Verification

Before concluding a delegated task, confirm:
1. Every required subagent was actually spawned and either completed or explicitly reported its failure.
2. Material reviewer findings and conflicting evidence were resolved.
3. Final diff was inspected for unintended edits.
4. Relevant targeted tests, syntax/type checks, or builds ran and passed, and any check that could not run is explicitly stated.
5. No required subagent is still running, and no claimed delegation occurred without a real `invoke_subagent` (or `/swarm`) call.
