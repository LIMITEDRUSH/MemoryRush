# MemoryRush Agent Instructions

These instructions apply to every task in this repository.

## Context Check

When a task concerns project requirements, architecture, implementation, progress, or the next development step:

1. Consult the relevant sections of `docs/PROJECT_CONTEXT_CN.md`. It is the primary collaboration and project-memory file.
2. Consult `docs/RESEARCH_SPEC_CN.md` for requirements and `docs/RESEARCH_PLAN_CN.md` for phase ordering when the task concerns design or implementation.
3. Check `tasks/plan_CN.md` and `tasks/todo_CN.md` before reporting progress or selecting the next task.
4. Distinguish planned behavior, locally implemented behavior, verified behavior, committed behavior, and behavior already pushed to GitHub.

Do not read the project-context files for every simple or unrelated answer. Load only the context needed for the current task.

If an explicitly confirmed requirement, architecture decision, development-route change, or collaboration preference changes, update both `docs/PROJECT_CONTEXT.md` and `docs/PROJECT_CONTEXT_CN.md`. Do not record tentative brainstorming as an accepted decision.

## Collaboration Rules

- Communicate with the user in Chinese unless another language is requested.
- Teach while developing. Explain the goal, principle, data flow, choices, trade-offs, and known problems so a beginner can follow the work.
- Before any project implementation, file edit, state-changing command, model run, installation, commit, or push, present a concise action checklist and wait for the user's explicit confirmation.
- The checklist must state the goal and scope, likely files or commands, and verification. Approval covers only the listed scope; request confirmation again if the scope expands materially.
- Explanations, direct answers, and the minimal read-only inspection needed to prepare a checklist do not require confirmation.
- After a checklist is shown, the user's reply of "确认", "开始", or "继续" counts as approval.
- Do not commit or push unless it was explicitly included in the approved checklist.
- Do not present an LLM-generated score, confidence value, or answer as objective truth. Identify its source and validation status.
- Keep MemoryRush a personal, local-first, research-oriented AI/ML engineering project. Do not add commercial product assumptions.

## Source-Of-Truth Order

When files disagree, use this order:

1. The user's latest explicit instruction.
2. `docs/PROJECT_CONTEXT_CN.md`.
3. `docs/RESEARCH_SPEC_CN.md`.
4. `docs/RESEARCH_PLAN_CN.md`.
5. `tasks/plan_CN.md` and `tasks/todo_CN.md`.
6. Older `MemoryPoint_*` documents, which are background material only.

## 中文说明

本文件是 Codex 在 MemoryRush 仓库中的入口说明。只有任务涉及项目需求、架构、实现、进度或下一步开发时，才按需读取 `docs/PROJECT_CONTEXT_CN.md` 的相关部分，并按上面的 source-of-truth 顺序核对状态。项目工作执行前必须先列出行动清单并等待用户确认；解释、答疑和制定清单所需的最小只读检查除外。简单或无关回答不要求读取项目上下文文件。
