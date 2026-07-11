# ADR 0004 — Organization / Workspace Extension Points

## Status
Accepted (M1)

## Context
AIOS must eventually support multiple Organizations → Workspaces → (Channels, Tasks, Agents, Files, Knowledge, Activity). The backend today has only `Project`. We want the final UI architecture now, enabling functionality as the backend evolves — with no redesign.

## Decision
- Model the hierarchy in the frontend now (`features/workspace/types.ts`): `Organization`, `WorkspaceSummary` (id, orgId, name, icon?, color?, isPinned, isFavorite, lastOpenedAt?, unreadCount?), `WorkspaceSwitcherState`.
- Map the current real `Project` → one `WorkspaceSummary`. **No fabricated/mock workspaces.**
- `WorkspaceSwitcher` renders the final component tree (org header, search, pinned/favorites/recent sections, all-workspaces, new-workspace, settings) but gates behavior behind capability flags derived from data:
  - `canCreateWorkspace = false` (until backend) → "+ New Workspace" shown disabled ("Coming soon")
  - `canSwitchWorkspace = workspaces.length > 1`
  - `canSearchWorkspaces = workspaces.length > 1` (search input hidden when ≤ 1)
  - `canManageOrgs = false`
- Empty sections (pinned/favorites/recent) render only when non-empty.
- `onSwitchWorkspace` already calls the `switch_project` WS path (fixed in M1), so multi-workspace switching works the moment more workspaces exist.

## Consequences
- Enabling multi-org/multi-workspace later requires only: backend models + populating `organizations`/`workspaces` + flipping capability flags. No component redesign.
- Deferred (design extension points only, not built): org/department hierarchy, meetings, workflows, knowledge graph, plugin marketplace.
