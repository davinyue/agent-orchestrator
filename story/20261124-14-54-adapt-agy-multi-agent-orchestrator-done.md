# 适配 Antigravity (AGY) 多 Agent 协调体系

## 背景

当前仓库（`main` 分支）是面向 Codex CLI 的多 Agent 协调模板，使用 `.codex/config.toml`、`.codex/agents/*.toml` 以及基于 `spawn_agent` 的 `astra-orchestrator` 技能，并绑定 GPT-6 Astra / Sol / Luna 模型。
需要在新增的 `agy` 分支上将该仓库完整适配为 Antigravity（AGY）原生多 Agent 协调项目，并按指定模型组合配置角色拓扑。

## 目标

1. 从 `main` 新增并切换到 `agy` 分支。
2. 将配置结构、角色定义、编排技能、安装脚本、使用指南、Token 统计脚本及自动化测试全部适配为 Antigravity 原生体系。
3. 按要求配置模型拓扑：
   - 主 Agent（root / orchestrator）：**Gemini 4 Neon (Extra High)**（`gemini-4-neon-xhigh`）
   - 评审角色（`reviewer`）：**Gemini 4 Neon (Extra High)**（`gemini-4-neon-xhigh`）
   - 其余执行角色（`explorer`、`worker`、`tester`、`researcher`）：**Gemini 3.8 Flash (High)**（`gemini-3.8-flash-high`；在 `invoke_subagent` / `.agents/agents/*.md` 中遵循平台 schema 使用 `flash` 层级，在 `/swarm` 中按精确型号锁定）

## 范围

- `profiles/NeonXHigh-FlashHigh/` 与 `profiles/NeonXHigh-FlashHigh-max-2-subagents/`：
  - `agents/agents/{explorer,worker,tester,researcher,reviewer}.md`
  - `agents/skills/agy-orchestrator/SKILL.md`
  - `cli/settings.json`（Antigravity CLI 参考配置）
- `AGENTS.md`、`README.md`、`.gitignore`
- `setup.sh`、`setup.ps1`
- `guides/{full-orchestration,low-concurrency,complex-repo-work,fast-iteration,routine-coding,token-usage}.md`
- `scripts/token_usage.py`（适配 Antigravity `transcript.jsonl`）
- `tests/test_profiles.py`、`tests/test_token_usage.py`

## 非目标

- 不修改 `main` 分支，不自动推送远程分支。
- 不修改宿主机全局配置（如 `~/.gemini/config/config.json` 或 `~/.gemini/antigravity-cli/settings.json`）。
- 不伪造 Antigravity 不会读取的虚构配置文件或非法 frontmatter 字段值。

## 关键设计

1. **目录发现与安装布局**：Antigravity 自动发现工作区 `.agents/agents/<role>.md`、`.agents/skills/<skill>/SKILL.md` 和根目录 `AGENTS.md`，无需 `.codex/`。安装脚本安装 `.agents` 和 `AGENTS.md` 两个组件，并保留已有 `AGENTS.md` 内容与覆写确认机制。
2. **模型分层与精确锁定说明**：
   - Antigravity 自定义子 Agent YAML frontmatter 的 `model` 与 `invoke_subagent` 的 `Model` 仅接受 `inherit`、`flash_lite`、`flash`、`pro` 四个枚举值。
   - 因此 `reviewer.md` 设 `model: inherit`（在主模型为 `gemini-4-neon-xhigh` 时精确继承），其余执行角色设 `model: flash`；同时在 `SKILL.md` 与文档中提供 `/swarm` 精确模型锁定策略（`gemini-4-neon-xhigh` 与 `gemini-3.8-flash-high`）。
3. **工具白名单与只读隔离**：所有 `.agents/agents/*.md` 仅使用 Antigravity 已验证的原生工具名（`read_file`、`edit_file`、`write_file`、`run_command`、`manage_task`、`search_web`），避免未知工具名导致的子 Agent 挂起问题；`explorer`、`researcher`、`reviewer` 不授予文件写工具。
4. **Token 统计适配**：解析 `~/.gemini/antigravity/brain/<conversation-id>/.system_generated/logs/transcript.jsonl` 中的 `PLANNER_RESPONSE`（`input_tokens` 为未缓存输入、`cache_read_tokens` 为缓存命中输入、`output_tokens` 为输出）以及 `invoke_subagent` 工具调用与子会话 ID 关联。

## 验收标准

- [x] 处于新建的 `agy` 分支，`main` 分支保持原样。
- [x] 两套 AGY profile 均通过 `tests/test_profiles.py` 结构、frontmatter、JSON 与 `setup.sh` 端到端安装测试。
- [x] `scripts/token_usage.py` 通过 `tests/test_token_usage.py` 测试，并可解析本机真实 Antigravity `transcript.jsonl`。
- [x] 全仓文件为 LF 换行，无残留 Codex 配置或无效工具/模型字段。

## 任务清单

### 分析

- [x] 明确需求目标、范围和非目标
- [x] 核验 Antigravity 官方自定义系统、子 Agent schema、模型命名与 transcript 日志结构

### 实施

- [x] 创建 `agy` 分支并清理旧 Codex profiles
- [x] 编写两套 AGY profile（角色定义、技能与 CLI 参考配置）
- [x] 更新 `AGENTS.md`、`setup.sh`、`setup.ps1`、`README.md`、`guides/` 与 `.gitignore`
- [x] 适配 `scripts/token_usage.py` 与 `tests/`

### 验证

- [x] 运行 `python3 -m unittest discover -s tests -v`（9/9 通过）
- [x] 验证 `sh -n setup.sh` 语法通过，且 `scripts/token_usage.py --root f927fe48` 成功解析真实 Antigravity `transcript.jsonl`
- [x] 验证全仓文件均为 LF 换行且无 Codex 残留词

### 收尾

- [x] 更新需求文档进度并重命名为 `-done.md`
- [x] 按规范提交到 `agy` 分支

## 当前进度

所有实施与验证均已完成，需求记录已归档为 `-done.md`，准备提交至 `agy` 分支。

## 风险与阻塞

1. **子 Agent 精确模型粒度限制**：`invoke_subagent` 与 `.agents/agents/*.md` 仅支持 `inherit / flash_lite / flash / pro` 层级；精确锁定 `gemini-3.8-flash-high` 需使用 `/swarm` 模式（并在启动前通过 `swarm{action:"models"}` 核对账号可用模型列表）。
2. **模型退役时间风险**：据 Antigravity 官方模型文档，`Gemini 3.8 Flash` 计划于 **2026-11-30** 下线；下线后 `/swarm` 中的执行角色应切换为 `Gemini 4 Hydrogen (High)`（`gemini-4-hydrogen-high`），而 `.agents/agents/*.md` 中的 `model: flash` 会自动跟随平台 `flash` 层级。
3. **PowerShell 环境**：当前 Linux 环境未安装 `pwsh`，`setup.ps1` 未在运行时执行，已按 POSIX `setup.sh` 同构逻辑逐项核对，需在 Windows/PowerShell 环境下使用时按需复测。
