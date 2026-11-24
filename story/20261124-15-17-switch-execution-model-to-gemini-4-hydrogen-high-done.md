# 将执行角色目标模型切换为 Gemini 4 Hydrogen (High)

## 背景

此前在 `agy` 分支中，执行角色（`explorer`、`worker`、`tester`、`researcher`）目标模型为 `Gemini 3.8 Flash (High)`（`gemini-3.8-flash-high`）。用户要求统一调整为 `Gemini 4 Hydrogen (High)`（`gemini-4-hydrogen-high`）。

## 目标

1. 将预设目录重命名为 `profiles/NeonXHigh-HydrogenHigh` 与 `profiles/NeonXHigh-HydrogenHigh-max-2-subagents`。
2. 将 `AGENTS.md`、两套预设的 `SKILL.md`、`setup.sh`、`setup.ps1`、`README.md`、`guides/*` 及 `tests/*` 中所有 `Gemini 3.8 Flash (High)` / `gemini-3.8-flash-high` / `FlashHigh` 引用统一替换为 `Gemini 4 Hydrogen (High)` / `gemini-4-hydrogen-high` / `HydrogenHigh`，并移除已不适用的 Gemini 3.8 Flash 退役提醒。
3. 保持 `.agents/agents/*.md` 中符合 Antigravity schema 的 `model: flash`（执行角色）与 `model: inherit`（`reviewer`）配置不变。

## 范围

- `profiles/NeonXHigh-HydrogenHigh/` 与 `profiles/NeonXHigh-HydrogenHigh-max-2-subagents/`
- `AGENTS.md`、`README.md`、`setup.sh`、`setup.ps1`
- `guides/full-orchestration.md`、`guides/low-concurrency.md`、`guides/complex-repo-work.md`、`guides/fast-iteration.md`、`guides/routine-coding.md`、`guides/token-usage.md`
- `tests/test_profiles.py`、`tests/test_token_usage.py`

## 非目标

- 不修改 `main` 分支，不推送远程。
- 不修改已归档的历史需求文件。

## 关键设计

- 按官方模型标识使用 `gemini-4-hydrogen-high`（`Gemini 4 Hydrogen (High)`）。
- 在 `invoke_subagent` 与 `.agents/agents/*.md` 协议层保持合法模型层级 `flash`（执行角色）与 `inherit`（`reviewer` 继承 `gemini-4-neon-xhigh`）；在 `/swarm` 精确锁模路径与全部文档/测试中使用 `gemini-4-hydrogen-high`。

## 验收标准

- [x] 全仓（除历史 `story/`）无残留 `3.8`、`flash-high`、`FlashHigh` 引用。
- [x] `python3 -m unittest discover -s tests -v`（9/9）与 `sh -n setup.sh` 全部通过。
- [x] 全仓均为 LF 换行，并在 `agy` 分支提交干净 commit。

## 任务清单

### 分析

- [x] 扫描全仓 `3.8` / `FlashHigh` / `flash-high` 引用

### 实施

- [x] 重命名两套预设目录为 `NeonXHigh-HydrogenHigh` 与 `NeonXHigh-HydrogenHigh-max-2-subagents`
- [x] 更新 `SKILL.md`、`AGENTS.md`、`setup.sh`、`setup.ps1`、`README.md` 与 `guides/*`
- [x] 更新 `tests/test_profiles.py` 与 `tests/test_token_usage.py`

### 验证

- [x] 运行 `python3 -m unittest discover -s tests -v`（9/9 通过）、`sh -n setup.sh` 通过、残留词扫描与 LF 检查全部通过

### 收尾

- [x] 更新需求记录并归档为 `-done.md`
- [x] 提交至 `agy` 分支

## 当前进度

全部替换与验证已完成，需求文档已归档为 `-done.md`，准备提交至 `agy` 分支。

## 风险与阻塞

- 当前 Linux 环境未安装 `pwsh`，`setup.ps1` 未做运行时测试，已与 `setup.sh` 逐项核对一致。
