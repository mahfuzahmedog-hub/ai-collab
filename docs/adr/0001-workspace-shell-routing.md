# ADR 0001 — Persistent Workspace Shell & Routing

## Status
Accepted (M1)

## Context
The app was a single page (`/`) that mounted chat + sidebars. The AIOS vision requires a persistent workspace where switching between views (Chat, Tasks, Agents, Files, Activity) never tears down the WebSocket connection or component state.

## Decision
- Introduce a route group `app/workspace/[workspaceId]/`.
- `layout.tsx` is the **persistent boundary**: it opens the single WebSocket via `connect()` in a `useEffect([])` and renders `WorkspaceShell` around `{children}`. It never unmounts across tab changes.
- `page.tsx` reads `?tab=` via `useSearchParams()` (wrapped in `<Suspense>`) and renders the active tab view.
- Tab switching uses `router.replace(pathname?tab=…, { scroll: false })` — same route segment, so only the page re-renders; the layout (shell + WebSocket) stays mounted.
- Root `/` is a resolver that redirects to `/workspace/{id}?tab=chat` using the stored/generated project id.
- `/dashboard` is preserved unchanged (migrated into the Activity tab in M6).

## Consequences
- One WebSocket for the whole workspace lifetime; no reconnect churn on navigation.
- Deep links work (`?tab=`, later `?channel=`, `?agent=`).
- `workspaceId` in the path is currently cosmetic; the live connection is keyed by `project_id` via `getProjectId()`. When multi-workspace backend lands, the path id becomes authoritative with no routing redesign.
