import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.token_usage import extract_spawns, unquote_arg

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "token_usage.py"


def write_transcript(brain_dir: Path, conv_id: str, records: list[dict]) -> Path:
    path = brain_dir / conv_id / ".system_generated" / "logs" / "transcript.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    return path


class HelperTests(unittest.TestCase):
    def test_unquote_arg_handles_json_encoded_and_plain_strings(self):
        self.assertEqual(unquote_arg('"worker"'), "worker")
        self.assertEqual(unquote_arg("reviewer"), "reviewer")
        self.assertEqual(unquote_arg(None), "")

    def test_extract_spawns_pairs_invoke_subagent_calls_with_generic_outputs(self):
        records = [
            {
                "type": "PLANNER_RESPONSE",
                "tool_calls": [
                    {"name": "read_file", "args": {"Path": '"/tmp/a.py"'}},
                    {
                        "name": "invoke_subagent",
                        "args": {
                            "TypeName": '"worker"',
                            "Role": '"Backend Worker"',
                            "Model": '"flash"',
                        },
                    },
                    {
                        "name": "invoke_subagent",
                        "args": {
                            "TypeName": '"reviewer"',
                            "Role": '"Security Reviewer"',
                            "Model": '"inherit"',
                        },
                    },
                ],
            },
            {"type": "GENERIC", "content": "file contents"},
            {
                "type": "GENERIC",
                "content": "Launched subagent with conversationId: 11111111-2222-3333-4444-555555555555",
            },
            {
                "type": "GENERIC",
                "content": '{"conversationId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"}',
            },
        ]
        spawns = extract_spawns(records)
        self.assertEqual(
            spawns,
            [
                {
                    "child_id": "11111111-2222-3333-4444-555555555555",
                    "type_name": "worker",
                    "role": "Backend Worker",
                    "requested_model": "flash",
                },
                {
                    "child_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    "type_name": "reviewer",
                    "role": "Security Reviewer",
                    "requested_model": "inherit",
                },
            ],
        )


class TokenUsageCliTests(unittest.TestCase):
    def build_sample_brain(self, brain_dir: Path) -> tuple[str, str, str]:
        root_id = "f927fe48-b04e-4f2e-8df1-bc7591ccc991"
        worker_id = "11111111-2222-3333-4444-555555555555"
        reviewer_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

        write_transcript(
            brain_dir,
            root_id,
            [
                {
                    "type": "USER_INPUT",
                    "created_at": "2026-11-24T06:54:53Z",
                    "content": "Implement invoice export.",
                },
                {
                    "type": "PLANNER_RESPONSE",
                    "created_at": "2026-11-24T06:55:00Z",
                    "model": "gemini-4-neon-xhigh",
                    "input_tokens": 1000,
                    "cache_read_tokens": 9000,
                    "output_tokens": 200,
                    "tool_calls": [
                        {
                            "name": "invoke_subagent",
                            "args": {
                                "TypeName": '"worker"',
                                "Role": '"Invoice Worker"',
                                "Model": '"flash"',
                            },
                        },
                        {
                            "name": "invoke_subagent",
                            "args": {
                                "TypeName": '"reviewer"',
                                "Role": '"Diff Reviewer"',
                                "Model": '"inherit"',
                            },
                        },
                    ],
                },
                {"type": "GENERIC", "content": f"conversationId: {worker_id}"},
                {"type": "GENERIC", "content": f"conversationId: {reviewer_id}"},
            ],
        )
        write_transcript(
            brain_dir,
            worker_id,
            [
                {
                    "type": "PLANNER_RESPONSE",
                    "created_at": "2026-11-24T06:55:05Z",
                    "model": "gemini-4-hydrogen-high",
                    "input_tokens": 500,
                    "cache_read_tokens": 1500,
                    "output_tokens": 300,
                }
            ],
        )
        write_transcript(
            brain_dir,
            reviewer_id,
            [
                {
                    "type": "PLANNER_RESPONSE",
                    "created_at": "2026-11-24T06:56:00Z",
                    "model": "gemini-4-neon-xhigh",
                    "input_tokens": 400,
                    "cache_read_tokens": 1600,
                    "output_tokens": 100,
                }
            ],
        )
        return root_id, worker_id, reviewer_id

    def run_cli(self, *args: str) -> str:
        with tempfile.TemporaryDirectory() as directory:
            self.build_sample_brain(Path(directory))
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--brain-dir", directory, *args],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_list_counts_subagents_and_lists_models(self):
        output = self.run_cli("--list", "--date", "2026-11-24")
        self.assertRegex(
            output,
            r"2026-11-24 06:54\s+f927fe48\s+2\s+gemini-4-hydrogen-high, gemini-4-neon-xhigh",
        )

    def test_latest_renders_markdown_with_cache_hit_rate(self):
        output = self.run_cli("--latest")
        self.assertIn("3 (1 root, 2 subagent(s))", output)
        self.assertIn("| `f927fe48` | root | gemini-4-neon-xhigh |", output)
        self.assertIn("| `11111111` | worker (Invoice Worker) | gemini-4-hydrogen-high |", output)
        self.assertIn("| `aaaaaaaa` | reviewer (Diff Reviewer) | gemini-4-neon-xhigh |", output)
        # Total uncached = 1900, cached = 12100 -> 12100 / 14000 = 86.4%
        self.assertIn("Cache hit rate on input: 86.4%", output)

    def test_root_json_preserves_roles_and_totals(self):
        report = json.loads(self.run_cli("--root", "f927fe48", "--format", "json"))
        self.assertEqual(report["root"], "f927fe48-b04e-4f2e-8df1-bc7591ccc991")
        self.assertEqual(len(report["conversations"]), 3)
        self.assertEqual(
            {c["type_name"] for c in report["conversations"]},
            {"root", "worker", "reviewer"},
        )
        total_tokens = sum(
            usage["total_tokens"]
            for conv in report["conversations"]
            for usage in conv["per_model"].values()
        )
        # (1000+9000+200) + (500+1500+300) + (400+1600+100) = 10200 + 2300 + 2100 = 14600
        self.assertEqual(total_tokens, 14600)


if __name__ == "__main__":
    unittest.main()
