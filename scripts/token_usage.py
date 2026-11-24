#!/usr/bin/env python3
"""Aggregate Antigravity (AGY) token usage for an orchestrated conversation.

Antigravity writes one structured JSONL transcript per conversation under:
  ~/.gemini/antigravity/brain/<conversation-id>/.system_generated/logs/transcript.jsonl

Parent conversations record `invoke_subagent` tool calls alongside the spawned
subagent's `conversationId`, so walking those links aggregates the full cost of
an orchestrated session split by conversation, role, and model.

Usage:
  scripts/token_usage.py --list [--date YYYY-MM-DD]
  scripts/token_usage.py --root <conversation-id-or-prefix> [--format md|json]
  scripts/token_usage.py --latest

Standard library only. Read-only: it never modifies transcript files.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

USAGE_KEYS = (
    "uncached_input_tokens",
    "cache_read_tokens",
    "output_tokens",
    "total_tokens",
)

CONVERSATION_ID_RE = re.compile(
    r"""(?:conversationId|conversation_id)\s*[:=]\s*["']?([0-9a-fA-F]{8}-[0-9a-fA-F-]{4,}|[A-Za-z0-9_-]{6,})["']?"""
)
UUID_RE = re.compile(
    r"\b([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\b"
)


def empty_usage() -> dict[str, int]:
    return {k: 0 for k in USAGE_KEYS}


def add_usage(target: dict[str, int], usage: dict[str, int]) -> None:
    for key in USAGE_KEYS:
        target[key] += int(usage.get(key) or 0)


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def unquote_arg(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        text = value.strip()
        if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
            try:
                decoded = json.loads(text)
                if isinstance(decoded, str):
                    return decoded
            except json.JSONDecodeError:
                pass
        return text
    return str(value)


def extract_conversation_id(content: str) -> str | None:
    if not content:
        return None
    match = CONVERSATION_ID_RE.search(content)
    if match:
        return match.group(1)
    uuid_match = UUID_RE.search(content)
    if uuid_match:
        return uuid_match.group(1)
    return None


def iter_transcripts(brain_dir: Path):
    if not brain_dir.is_dir():
        return
    for entry in sorted(brain_dir.iterdir()):
        if not entry.is_dir():
            continue
        transcript = entry / ".system_generated" / "logs" / "transcript.jsonl"
        if transcript.is_file():
            yield entry.name, transcript


def extract_spawns(records: list[dict]) -> list[dict[str, str]]:
    """Extract subagent spawns by pairing invoke_subagent calls with tool outputs."""
    spawns: list[dict[str, str]] = []
    seen_children: set[str] = set()

    for idx, obj in enumerate(records):
        if obj.get("type") != "PLANNER_RESPONSE":
            continue
        tool_calls = obj.get("tool_calls") or []
        if not isinstance(tool_calls, list) or not tool_calls:
            continue

        generic_outputs: list[dict] = []
        cursor = idx + 1
        while cursor < len(records) and len(generic_outputs) < len(tool_calls):
            nxt = records[cursor]
            if nxt.get("type") == "PLANNER_RESPONSE":
                break
            if nxt.get("type") == "GENERIC":
                generic_outputs.append(nxt)
            cursor += 1

        for call_idx, call in enumerate(tool_calls):
            if not isinstance(call, dict) or call.get("name") != "invoke_subagent":
                continue
            args = call.get("args") or {}
            if not isinstance(args, dict):
                args = {}
            child_id = None
            if call_idx < len(generic_outputs):
                child_id = extract_conversation_id(str(generic_outputs[call_idx].get("content") or ""))
            if not child_id:
                for out in generic_outputs:
                    candidate = extract_conversation_id(str(out.get("content") or ""))
                    if candidate and candidate not in seen_children:
                        child_id = candidate
                        break
            if not child_id or child_id in seen_children:
                continue
            seen_children.add(child_id)
            spawns.append(
                {
                    "child_id": child_id,
                    "type_name": unquote_arg(args.get("TypeName")) or "subagent",
                    "role": unquote_arg(args.get("Role")),
                    "requested_model": unquote_arg(args.get("Model")),
                }
            )
    return spawns


def analyze_conversation(conv_id: str, path: Path) -> dict:
    records: list[dict] = []
    per_model: dict[str, dict[str, int]] = defaultdict(empty_usage)
    responses: dict[str, int] = defaultdict(int)
    first_ts: datetime | None = None
    last_ts: datetime | None = None
    last_model: str | None = None

    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            records.append(obj)
            ts = parse_ts(obj.get("created_at") or obj.get("timestamp"))
            if ts:
                if first_ts is None or ts < first_ts:
                    first_ts = ts
                if last_ts is None or ts > last_ts:
                    last_ts = ts
            if obj.get("type") == "PLANNER_RESPONSE":
                model = obj.get("model") or last_model or "unknown"
                last_model = obj.get("model") or last_model
                has_usage = any(
                    k in obj for k in ("input_tokens", "cache_read_tokens", "output_tokens")
                )
                if has_usage:
                    uncached = int(obj.get("input_tokens") or 0)
                    cached = int(obj.get("cache_read_tokens") or 0)
                    output = int(obj.get("output_tokens") or 0)
                    usage = {
                        "uncached_input_tokens": uncached,
                        "cache_read_tokens": cached,
                        "output_tokens": output,
                        "total_tokens": uncached + cached + output,
                    }
                    add_usage(per_model[model], usage)
                    responses[model] += 1

    return {
        "id": conv_id,
        "parent_id": None,
        "type_name": "root",
        "role": "root",
        "requested_model": "",
        "model": last_model,
        "started": first_ts,
        "ended": last_ts,
        "per_model": dict(per_model),
        "responses": dict(responses),
        "spawns": extract_spawns(records),
        "path": str(path),
    }


def collect_conversations(brain_dir: Path) -> dict[str, dict]:
    conversations: dict[str, dict] = {}
    for conv_id, path in iter_transcripts(brain_dir):
        conversations[conv_id] = analyze_conversation(conv_id, path)

    for conv_id, conv in conversations.items():
        for spawn in conv["spawns"]:
            child = conversations.get(spawn["child_id"])
            if not child or child["id"] == conv_id:
                continue
            child["parent_id"] = conv_id
            child["type_name"] = spawn["type_name"] or "subagent"
            child["role"] = spawn["role"] or spawn["type_name"] or "subagent"
            child["requested_model"] = spawn["requested_model"]

    return conversations


def collect_session_tree(root_id: str, conversations: dict[str, dict]) -> list[dict]:
    """Collect a root conversation and all reachable descendant subagents."""
    result: list[dict] = []
    visited: set[str] = set()

    def walk(conv_id: str) -> None:
        if conv_id in visited or conv_id not in conversations:
            return
        visited.add(conv_id)
        conv = conversations[conv_id]
        result.append(conv)
        for spawn in conv["spawns"]:
            walk(spawn["child_id"])

    walk(root_id)
    if len(result) > 1:
        root_conv = result[0]
        children = sorted(
            result[1:],
            key=lambda c: c["started"] or datetime.max.replace(tzinfo=timezone.utc),
        )
        return [root_conv, *children]
    return result


def matches_date(conv: dict, date: str | None) -> bool:
    if not date:
        return True
    started = conv.get("started")
    if not started:
        return False
    return started.astimezone(timezone.utc).strftime("%Y-%m-%d") == date


def fmt_int(n: int) -> str:
    return f"{n:,}"


def fmt_duration(start: datetime | None, end: datetime | None) -> str:
    if not start or not end:
        return "-"
    seconds = max(0, int((end - start).total_seconds()))
    return f"{seconds // 60}m{seconds % 60:02d}s"


def role_label(conv: dict) -> str:
    if conv["parent_id"] is None:
        return "root"
    if conv["role"] and conv["role"] != conv["type_name"]:
        return f"{conv['type_name']} ({conv['role']})"
    return conv["type_name"] or "subagent"


def render_markdown(root_id: str, threads: list[dict]) -> str:
    starts = [t["started"] for t in threads if t["started"]]
    ends = [t["ended"] for t in threads if t["ended"]]
    wall = fmt_duration(min(starts), max(ends)) if starts and ends else "-"
    subagent_count = max(0, len(threads) - 1)

    lines: list[str] = []
    lines.append(f"### Conversation `{root_id[:8]}`")
    lines.append("")
    lines.append(f"- conversations: {len(threads)} (1 root, {subagent_count} subagent(s))")
    lines.append(f"- wall time: {wall}")
    lines.append("")

    lines.append(
        "| Conversation | Role | Model | Responses | Uncached in | Cached in | Output | Total | Duration |"
    )
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|")

    grand = empty_usage()
    by_model: dict[str, dict[str, int]] = defaultdict(empty_usage)
    by_model_responses: dict[str, int] = defaultdict(int)
    for conv in threads:
        for model, usage in sorted(conv["per_model"].items()):
            lines.append(
                f"| `{conv['id'][:8]}` | {role_label(conv)} | {model} | "
                f"{conv['responses'].get(model, 0)} | "
                f"{fmt_int(usage['uncached_input_tokens'])} | "
                f"{fmt_int(usage['cache_read_tokens'])} | "
                f"{fmt_int(usage['output_tokens'])} | "
                f"{fmt_int(usage['total_tokens'])} | "
                f"{fmt_duration(conv['started'], conv['ended'])} |"
            )
            add_usage(grand, usage)
            add_usage(by_model[model], usage)
            by_model_responses[model] += conv["responses"].get(model, 0)
    lines.append("")

    lines.append("| Model | Conversations | Responses | Uncached in | Cached in | Output | Total |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for model, usage in sorted(by_model.items()):
        n_convs = sum(1 for conv in threads if model in conv["per_model"])
        lines.append(
            f"| {model} | {n_convs} | {by_model_responses[model]} | "
            f"{fmt_int(usage['uncached_input_tokens'])} | "
            f"{fmt_int(usage['cache_read_tokens'])} | "
            f"{fmt_int(usage['output_tokens'])} | "
            f"{fmt_int(usage['total_tokens'])} |"
        )
    lines.append(
        f"| **all** | {len(threads)} | {sum(by_model_responses.values())} | "
        f"{fmt_int(grand['uncached_input_tokens'])} | "
        f"{fmt_int(grand['cache_read_tokens'])} | "
        f"{fmt_int(grand['output_tokens'])} | "
        f"{fmt_int(grand['total_tokens'])} |"
    )

    total_input = grand["uncached_input_tokens"] + grand["cache_read_tokens"]
    if total_input:
        pct = 100.0 * grand["cache_read_tokens"] / total_input
        lines.append("")
        lines.append(f"Cache hit rate on input: {pct:.1f}%")
    return "\n".join(lines)


def to_json(root_id: str, threads: list[dict]) -> str:
    def clean(conv: dict) -> dict:
        out = {k: v for k, v in conv.items() if k != "spawns"}
        out["started"] = conv["started"].isoformat() if conv["started"] else None
        out["ended"] = conv["ended"].isoformat() if conv["ended"] else None
        out["role_label"] = role_label(conv)
        out["spawned_ids"] = [s["child_id"] for s in conv["spawns"]]
        return out

    return json.dumps({"root": root_id, "conversations": [clean(c) for c in threads]}, indent=2)


def list_conversations(conversations: dict[str, dict], date: str | None, limit: int) -> None:
    rows = []
    for conv_id, conv in conversations.items():
        if conv["parent_id"] is not None:
            continue
        if not matches_date(conv, date):
            continue
        tree = collect_session_tree(conv_id, conversations)
        n_sub = max(0, len(tree) - 1)
        models = sorted({m for c in tree for m in c["per_model"]})
        started = conv["started"] or datetime.min.replace(tzinfo=timezone.utc)
        rows.append((started, conv_id, n_sub, ", ".join(models) or "-"))

    rows.sort(reverse=True)
    print("started (UTC)       root id   subagents  models")
    for started, conv_id, n_sub, models in rows[:limit]:
        ts = started.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")
        print(f"{ts:<19} {conv_id[:8]}  {n_sub:>9}  {models}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--brain-dir",
        default=os.path.expanduser("~/.gemini/antigravity/brain"),
        help="Path to Antigravity brain directory containing conversation folders.",
    )
    parser.add_argument(
        "--date",
        help="Filter root conversations started on this UTC date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List root conversations and their subagent counts.",
    )
    parser.add_argument("--limit", type=int, default=20, help="Rows to show with --list.")
    parser.add_argument("--root", help="Conversation ID (or unique prefix) to report on.")
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Report on the most recent root conversation that spawned subagents.",
    )
    parser.add_argument("--format", choices=("md", "json"), default="md")
    args = parser.parse_args(argv)

    brain_dir = Path(args.brain_dir)
    if not brain_dir.is_dir():
        print(f"brain dir not found: {brain_dir}", file=sys.stderr)
        return 2

    conversations = collect_conversations(brain_dir)
    if not conversations:
        print("no Antigravity transcripts found", file=sys.stderr)
        return 1

    if args.list:
        list_conversations(conversations, args.date, args.limit)
        return 0

    root_id = None
    if args.root:
        matches = [
            cid
            for cid, conv in conversations.items()
            if cid.startswith(args.root) and matches_date(conv, args.date)
        ]
        if len(matches) != 1:
            print(f"--root matched {len(matches)} conversations; give a longer prefix", file=sys.stderr)
            return 2
        root_id = matches[0]
    elif args.latest:
        candidates = []
        for cid, conv in conversations.items():
            if conv["parent_id"] is not None or not matches_date(conv, args.date):
                continue
            tree = collect_session_tree(cid, conversations)
            if len(tree) > 1:
                started = conv["started"] or datetime.min.replace(tzinfo=timezone.utc)
                candidates.append((started, cid))
        if not candidates:
            print("no conversation with subagents found", file=sys.stderr)
            return 1
        root_id = max(candidates)[1]
    else:
        parser.print_help()
        return 2

    threads = collect_session_tree(root_id, conversations)
    if args.format == "json":
        print(to_json(root_id, threads))
    else:
        print(render_markdown(root_id, threads))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
