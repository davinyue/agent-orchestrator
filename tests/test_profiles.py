import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILES = {
    "NeonXHigh-FlashHigh": 4,
    "NeonXHigh-FlashHigh-max-2-subagents": 2,
}
FLASH_ROLES = ("explorer", "researcher", "tester", "worker")
READ_ONLY_ROLES = ("explorer", "researcher", "reviewer")
WRITE_ROLES = ("worker", "tester")
ALL_ROLES = (*FLASH_ROLES, "reviewer")
VALID_SUBAGENT_MODELS = {"inherit", "flash_lite", "flash", "pro"}
VALID_AGY_TOOLS = {
    "read_file",
    "edit_file",
    "write_file",
    "run_command",
    "manage_task",
    "search_web",
}
FORBIDDEN_CODEX_MARKERS = (".codex", "spawn_agent", "gpt-6", "astra-orchestrator")


def parse_frontmatter(markdown_text: str) -> tuple[dict, str]:
    """Parse simple YAML frontmatter (scalars and single-level lists) using stdlib only."""
    lines = markdown_text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise AssertionError("Missing opening YAML frontmatter delimiter")
    end_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx is None:
        raise AssertionError("Missing closing YAML frontmatter delimiter")

    data: dict = {}
    current_list_key: str | None = None
    for raw_line in lines[1:end_idx]:
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if raw_line.startswith("  - ") or raw_line.startswith("- "):
            if current_list_key is None:
                raise AssertionError(f"List item without key: {raw_line}")
            item = raw_line.split("- ", 1)[1].strip().strip('"').strip("'")
            data[current_list_key].append(item)
            continue
        current_list_key = None
        if ":" not in raw_line:
            raise AssertionError(f"Invalid frontmatter line: {raw_line}")
        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            data[key] = []
            current_list_key = key
        elif value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = (
                [part.strip().strip('"').strip("'") for part in inner.split(",") if part.strip()]
                if inner
                else []
            )
        elif value == "true":
            data[key] = True
        elif value == "false":
            data[key] = False
        else:
            data[key] = value.strip('"').strip("'")

    body = "\n".join(lines[end_idx + 1 :])
    return data, body


class AntigravityProfileTests(unittest.TestCase):
    def test_profile_agents_skills_and_cli_settings(self):
        for profile, concurrency in PROFILES.items():
            with self.subTest(profile=profile):
                directory = ROOT / "profiles" / profile
                self.assertFalse((directory / "codex").exists())

                for role in ALL_ROLES:
                    agent_path = directory / "agents" / "agents" / f"{role}.md"
                    self.assertTrue(agent_path.is_file(), f"Missing {agent_path}")
                    text = agent_path.read_text(encoding="utf-8")
                    meta, body = parse_frontmatter(text)
                    self.assertEqual(meta["name"], role)
                    self.assertTrue(meta["description"])
                    self.assertIs(meta["subagent"], True)
                    self.assertIs(meta["mainAgent"], False)
                    self.assertEqual(meta["commandExecutionPolicy"], "sandbox")
                    self.assertIn(meta["model"], VALID_SUBAGENT_MODELS)

                    expected_model = "inherit" if role == "reviewer" else "flash"
                    self.assertEqual(meta["model"], expected_model)

                    tools = set(meta["tools"])
                    self.assertTrue(tools, f"{role} must declare explicit tools")
                    self.assertTrue(
                        tools.issubset(VALID_AGY_TOOLS),
                        f"{role} contains unsupported tools: {tools - VALID_AGY_TOOLS}",
                    )
                    self.assertIn("read_file", tools)
                    if role in READ_ONLY_ROLES:
                        self.assertNotIn("edit_file", tools)
                        self.assertNotIn("write_file", tools)
                    if role in WRITE_ROLES:
                        self.assertIn("edit_file", tools)
                        self.assertIn("write_file", tools)
                    if role == "researcher":
                        self.assertIn("search_web", tools)
                    self.assertTrue(body.strip())
                    for marker in FORBIDDEN_CODEX_MARKERS:
                        self.assertNotIn(marker, text.lower())

                skill_path = directory / "agents" / "skills" / "agy-orchestrator" / "SKILL.md"
                self.assertTrue(skill_path.is_file())
                skill_text = skill_path.read_text(encoding="utf-8")
                skill_meta, _ = parse_frontmatter(skill_text)
                self.assertEqual(skill_meta["name"], "agy-orchestrator")
                self.assertTrue(skill_meta["description"])
                self.assertIn("gemini-4-neon-xhigh", skill_text)
                self.assertIn("gemini-3.8-flash-high", skill_text)
                self.assertIn("invoke_subagent", skill_text)
                self.assertIn("/swarm", skill_text)
                self.assertIn(f"**{concurrency}**", skill_text)
                for marker in FORBIDDEN_CODEX_MARKERS:
                    self.assertNotIn(marker, skill_text.lower())

                settings_path = directory / "cli" / "settings.json"
                settings = json.loads(settings_path.read_text(encoding="utf-8"))
                self.assertEqual(
                    settings["$schema"], "https://antigravity.google/schemas/v1/settings.json"
                )
                self.assertEqual(settings["model"], "Gemini 4 Neon (XHigh)")
                self.assertEqual(settings["agentMode"], "auto")
                self.assertEqual(settings["toolPermission"], "proceed-in-sandbox")
                self.assertIs(settings["enableTerminalSandbox"], True)

    def test_root_agents_md_has_no_codex_remnants(self):
        agents_md = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("agy-orchestrator", agents_md)
        self.assertIn("Gemini 4 Neon (Extra High)", agents_md)
        self.assertIn("Gemini 3.8 Flash (High)", agents_md)
        self.assertIn("invoke_subagent", agents_md)
        for marker in FORBIDDEN_CODEX_MARKERS:
            self.assertNotIn(marker, agents_md.lower())

    def test_installers_select_profiles_and_install_agy_layout(self):
        installers = [("shell", ["sh", str(ROOT / "setup.sh")])]
        if shutil.which("pwsh"):
            installers.append(("powershell", ["pwsh", "-NoProfile", "-File", str(ROOT / "setup.ps1")]))
        choices = (
            ("", "NeonXHigh-FlashHigh"),
            ("1", "NeonXHigh-FlashHigh"),
            ("NeonXHigh-FlashHigh", "NeonXHigh-FlashHigh"),
            ("neonxhigh-flashhigh", "NeonXHigh-FlashHigh"),
            ("2", "NeonXHigh-FlashHigh-max-2-subagents"),
            ("max-2", "NeonXHigh-FlashHigh-max-2-subagents"),
            ("NeonXHigh-FlashHigh-max-2-subagents", "NeonXHigh-FlashHigh-max-2-subagents"),
        )
        for installer, command in installers:
            for choice, profile in choices:
                with self.subTest(installer=installer, choice=choice), tempfile.TemporaryDirectory() as target:
                    result = subprocess.run(
                        command,
                        input=f"{target}\n{choice}\n\n\n",
                        text=True,
                        capture_output=True,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn("Select Profile [1-2] (default 1):", result.stdout)
                    self.assertIn(f"profile: {profile}", result.stdout)
                    self.assertIn("2 component(s) installed", result.stdout)

                    target_path = Path(target)
                    self.assertFalse((target_path / ".codex").exists())
                    source = ROOT / "profiles" / profile / "agents"
                    for role in ALL_ROLES:
                        rel = Path("agents") / f"{role}.md"
                        self.assertEqual(
                            (target_path / ".agents" / rel).read_text(encoding="utf-8"),
                            (source / rel).read_text(encoding="utf-8"),
                        )
                    skill_rel = Path("skills") / "agy-orchestrator" / "SKILL.md"
                    self.assertEqual(
                        (target_path / ".agents" / skill_rel).read_text(encoding="utf-8"),
                        (source / skill_rel).read_text(encoding="utf-8"),
                    )
                    self.assertEqual(
                        (target_path / "AGENTS.md").read_text(encoding="utf-8"),
                        (ROOT / "AGENTS.md").read_text(encoding="utf-8"),
                    )

    def test_installer_preserves_existing_agents_md_without_duplication(self):
        with tempfile.TemporaryDirectory() as target:
            agents_file = Path(target) / "AGENTS.md"
            agents_file.write_text("# Existing project rules\n\nKeep tests green.\n", encoding="utf-8")

            first = subprocess.run(
                ["sh", str(ROOT / "setup.sh")],
                input=f"{target}\n1\nn\ny\n",
                text=True,
                capture_output=True,
            )
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertIn("Appended instructions to AGENTS.md", first.stdout)
            combined = agents_file.read_text(encoding="utf-8")
            self.assertIn("# Existing project rules", combined)
            self.assertIn("agy-orchestrator", combined)

            second = subprocess.run(
                ["sh", str(ROOT / "setup.sh")],
                input=f"{target}\n1\nn\ny\n",
                text=True,
                capture_output=True,
            )
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertIn("Skipped AGENTS.md: instructions already present.", second.stdout)
            self.assertEqual(agents_file.read_text(encoding="utf-8"), combined)


if __name__ == "__main__":
    unittest.main()
