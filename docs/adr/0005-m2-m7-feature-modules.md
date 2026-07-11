# ADR 0005 — M2–M7 Feature Modules (Communication, Kanban, Agents, Notifications, Search, Activity)

## Status
Accepted (M2–M7). Built but not yet deployed (holding for explicit release).

## Context
With the persistent Workspace Shell (ADR-0001) in place, M2–M7 fill the tabs with production features against the real FastAPI/WebSocket backend.

## Decisions

### Backend contract additions (`handlers.py`, `repository.py`)
- Commands: `create_task`, `update_task` (drag/drawer), `pause_agent`, `resume_agent`, `mark_notification_read`, `read_file`.
- Repository: `load_project_tasks`, `update_task_fields` (None = intentional clear), `get_file_content` (DB, filesystem fallback).
- `load_project` + `switch_project` now emit `task_list`.
- Broadcasts: `task_created`, `task_updated`, `notification_read`; response `file_content`.

### Frontend feature modules (`frontend/src/features/*`)
- `chat/` — `MessageComposer` (markdown, @mention autocomplete, mentions sent, attachment UI disabled), `Markdown` (react-markdown + remark-gfm), `MessageActions` (edit/delete for user msgs).
- `tasks/` — `KanbanBoard` (@dnd-kit, 7 columns mapping the 11 lifecycle statuses → columns; drop → `update_task`), `TaskDrawer` (create/edit).
- `files/` — `FilesTab` (tree + viewer), `FileViewer` (`read_file`, cached in store).
- `agents/` — `AgentProfile` drawer (status, skills, mission, recent logs, private chat, pause/resume). AgentCard opens it.
- `notifications/` — `NotificationCenter` (filter, mark read/all, deep-link).
- `search/` — `CommandPalette` (cmdk, Cmd/Ctrl+K; go-to tab/channel/agent/task).
- `activity/` — `ActivityTab` (dashboard parity: stat cards + lifecycle + logs + agents table).

### Kanban ↔ lifecycle (per prior decision)
Lifecycle is the source of truth. Columns are a visualization; dropping applies the column's representative status. No duplicate task statuses introduced.

### Store
Added `fileContents`, `selectedFile`, `notificationsOpen`, `activeAgentProfile` (+setters), `markAllNotificationsRead`. `addTask`/`addThread`/`addMessage`/`addChannel` dedupe by id. `case "message"` stores all messages (no channel drop).

### Polish (M7)
TabBar `role=tablist`/`aria-selected`/focus rings; Timeline renders last 300 messages (perf cap; upgrade path = react-window); framer-motion transitions in drawers.

### `/dashboard`
Kept working; superseded by the Activity tab. Deprecate later once fully redundant.

## Consequences
- All existing power is now reachable via the persistent tabbed shell.
- Deferred (extension points only): orgs/departments, meetings, workflows, knowledge graph, tool center, plugin marketplace, file uploads (attachment UI shipped disabled pending storage backend).
