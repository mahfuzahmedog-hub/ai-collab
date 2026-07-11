# ADR 0002 — Feature-Module Structure

## Status
Accepted (M1)

## Context
Components were grouped by generic type (`components/layout`, `components/timeline`). As AIOS grows (tasks, agents, notifications, search, knowledge, tools), a feature-oriented structure keeps related UI + logic together and separates presentation from business logic.

## Decision
- New feature modules live under `frontend/src/features/<feature>/`.
- M1 adds `features/workspace/` (shell, header, tabbar, statusbar, rail, main view, workspace switcher, types).
- Existing components under `components/**` are **reused as-is** (imported, not rewritten): `layout/LeftNav`, `layout/AgentSidebar`, `timeline/Timeline`, `approvals/ApprovalDialog`, `tasks/Panel`, `agents/Panel`.
- Business logic stays in `lib/ws` (WebSocket transport + handlers) and the zustand `store/`. Feature components are presentational and read/write through the store.

## Consequences
- Future milestones add sibling modules (`features/chat`, `features/tasks`, `features/agents`, `features/notifications`, `features/search`) without touching unrelated code.
- Gradual migration: existing `components/**` can be moved into feature modules opportunistically; no big-bang refactor.
