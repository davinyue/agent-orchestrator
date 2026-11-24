# Token Usage

Usage in an orchestrated Antigravity session depends on repository size, how many subagents the root actually spawns, and prompt-cache hit rates. This guide explains what Antigravity records locally and how to aggregate root + subagent usage with `scripts/token_usage.py`.

## What Antigravity records

Each Antigravity conversation stores its structured transcript under:

```text
~/.gemini/antigravity/brain/<conversation-id>/.system_generated/logs/transcript.jsonl
```

Relevant fields in `transcript.jsonl`:

- `PLANNER_RESPONSE` entries: record `model`, `created_at`, `input_tokens` (uncached input tokens), `cache_read_tokens` (cached input tokens), `output_tokens`, and any `tool_calls`.
- `invoke_subagent` tool calls: record `TypeName`, `Role`, and `Model` in `tool_calls`, while the paired `GENERIC` tool result records the spawned subagent's `conversationId`.

Tracing `invoke_subagent` calls from a root conversation to each child conversation's `transcript.jsonl` gives the full token breakdown across root and all spawned subagents, split by conversation, role, and model.

## Measuring a run

`scripts/token_usage.py` is standard-library Python and strictly read-only.

```bash
# List root conversations and their spawned subagent counts
scripts/token_usage.py --list

# Filter to conversations started on a specific UTC date
scripts/token_usage.py --list --date 2026-11-24

# Report on one conversation (any unique conversation ID prefix works)
scripts/token_usage.py --root f927fe48

# Report on the most recent conversation that spawned subagents
scripts/token_usage.py --latest

# Machine-readable JSON output
scripts/token_usage.py --root f927fe48 --format json

# Point to a custom brain directory
scripts/token_usage.py --brain-dir ~/.gemini/antigravity/brain --list
```

## Reading the numbers

- **Uncached vs. cached input**: In Antigravity `transcript.jsonl`, `input_tokens` is uncached input and `cache_read_tokens` is cached input. Total input is `input_tokens + cache_read_tokens`, and cache hit rate is `cache_read_tokens / (input_tokens + cache_read_tokens)`.
- **Root overhead dominates long sessions**: Because the root stays alive on `gemini-4-neon-xhigh` across the full task, keeping subagent reports concise and avoiding unnecessary root turns saves far more quota than micro-optimizing a single Flash worker.
- **Parallelism trades tokens for latency**: Every concurrent subagent maintains and re-reads its own context. If quota is tight, use `NeonXHigh-FlashHigh-max-2-subagents`.

## Reducing usage

In rough order of impact:

1. **Skip orchestration for small edits**: Keep single-file fixes root-only or run directly on a fast model (see [routine-coding.md](routine-coding.md)).
2. **Cap concurrent subagents**: Use `NeonXHigh-FlashHigh-max-2-subagents` (max 2 active subagents).
3. **Reuse idle subagents**: Use `send_message` to follow up with an existing idle subagent instead of spawning a fresh conversation with a cold context.
4. **Keep subagent reports concise**: Ask for file paths, symbols, commands, pass/fail summaries, and risks rather than raw logs.
5. **Use `reviewer` selectively**: `reviewer` inherits `gemini-4-neon-xhigh`, so reserve it for non-trivial, high-risk, or multi-file changes.
