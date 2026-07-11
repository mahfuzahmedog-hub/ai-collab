"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useStore } from "@/store";
import { getProjectId } from "@/lib/websocket";
import { Check, Plus, Search, Settings } from "lucide-react";
import type { WorkspaceSummary, WorkspaceSwitcherState } from "./types";

// Single-workspace M1: derive the one real workspace from the active project.
// DO NOT fabricate mock workspaces — capability flags gate everything so enabling
// multi-workspace later is a data/flag change only, no UI redesign.
export function WorkspaceSwitcher() {
  const router = useRouter();
  const params = useParams();
  const project = useStore((s) => s.project);
  const activeProjectId = useStore((s) => s.activeProjectId);
  const [open, setOpen] = useState(false);

  const workspaceId =
    (params?.workspaceId as string) || activeProjectId || getProjectId();

  const workspaces: WorkspaceSummary[] = [
    {
      id: workspaceId,
      orgId: null,
      name: project?.title || "Workspace",
      isPinned: false,
      isFavorite: false,
    },
  ];

  const state: WorkspaceSwitcherState = {
    organizations: [],
    workspaces,
    activeOrgId: null,
    activeWorkspaceId: workspaceId,
    recent: [],
    pinned: [],
    favorites: [],
  };

  // Capability flags derived from data.
  const canCreateWorkspace = false;
  const canSwitchWorkspace = workspaces.length > 1;
  const canManageOrgs = false;
  const canSearchWorkspaces = workspaces.length > 1;

  const onSwitchWorkspace = (id: string) => {
    if (!canSwitchWorkspace || id === workspaceId) return;
    setOpen(false);
    router.replace(`/workspace/${id}?tab=chat`);
  };
  const onCreateWorkspace = () => {
    if (!canCreateWorkspace) return;
    setOpen(false);
  };
  const onSwitchOrg = () => {
    if (!canManageOrgs) return;
    setOpen(false);
  };

  const active = workspaces.find((w) => w.id === workspaceId) || workspaces[0];

  return (
    <div className="relative w-full flex flex-col items-center">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-9 h-9 rounded-lg bg-primary-600 flex items-center justify-center text-white font-bold text-sm hover:bg-primary-500 transition-colors"
        title={active?.name || "Workspace"}
      >
        {(active?.name || "W").charAt(0).toUpperCase()}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute top-11 left-0 z-50 w-72 bg-dark-900 border border-dark-700 rounded-lg shadow-2xl overflow-hidden animate-fade-in">
            <button
              disabled
              onClick={onSwitchOrg}
              className="w-full flex items-center justify-between px-3 py-2 border-b border-dark-700 text-dark-500 cursor-not-allowed"
            >
              <span className="text-xs font-semibold uppercase tracking-wider">
                Organization
              </span>
              <span className="text-[10px] text-dark-600">Coming soon</span>
            </button>

            {canSearchWorkspaces && (
              <div className="p-2 border-b border-dark-700">
                <div className="flex items-center gap-1.5 bg-dark-800 border border-dark-700 rounded px-2 py-1.5 text-dark-400">
                  <Search size={13} />
                  <input
                    placeholder="Search workspaces..."
                    className="bg-transparent text-white text-xs outline-none w-full"
                  />
                </div>
              </div>
            )}

            <div className="max-h-80 overflow-y-auto py-1">
              {state.pinned.length > 0 && (
                <>
                  <div className="px-2 py-1 text-[10px] uppercase tracking-wider text-dark-500">
                    Pinned
                  </div>
                  {state.pinned.map((w) => (
                    <WorkspaceRow
                      key={w.id}
                      w={w}
                      active={w.id === workspaceId}
                      onClick={() => onSwitchWorkspace(w.id)}
                    />
                  ))}
                </>
              )}
              {state.favorites.length > 0 && (
                <>
                  <div className="px-2 py-1 text-[10px] uppercase tracking-wider text-dark-500">
                    Favorites
                  </div>
                  {state.favorites.map((w) => (
                    <WorkspaceRow
                      key={w.id}
                      w={w}
                      active={w.id === workspaceId}
                      onClick={() => onSwitchWorkspace(w.id)}
                    />
                  ))}
                </>
              )}
              {state.recent.length > 0 && (
                <>
                  <div className="px-2 py-1 text-[10px] uppercase tracking-wider text-dark-500">
                    Recent
                  </div>
                  {state.recent.map((w) => (
                    <WorkspaceRow
                      key={w.id}
                      w={w}
                      active={w.id === workspaceId}
                      onClick={() => onSwitchWorkspace(w.id)}
                    />
                  ))}
                </>
              )}

              <div className="px-2 py-1 text-[10px] uppercase tracking-wider text-dark-500">
                Workspaces
              </div>
              {workspaces.map((w) => (
                <WorkspaceRow
                  key={w.id}
                  w={w}
                  active={w.id === workspaceId}
                  onClick={() => onSwitchWorkspace(w.id)}
                />
              ))}
            </div>

            <div className="border-t border-dark-700 p-1">
              <button
                disabled
                title="Coming soon"
                onClick={onCreateWorkspace}
                className="w-full flex items-center gap-2 px-2 py-1.5 text-sm text-dark-500 cursor-not-allowed"
              >
                <Plus size={14} /> New Workspace
                <span className="ml-auto text-[10px] text-dark-600">
                  Coming soon
                </span>
              </button>
              <button
                disabled
                title="Coming soon"
                className="w-full flex items-center gap-2 px-2 py-1.5 text-sm text-dark-500 cursor-not-allowed"
              >
                <Settings size={14} /> Workspace Settings
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function WorkspaceRow({
  w,
  active,
  onClick,
}: {
  w: WorkspaceSummary;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="w-full flex items-center gap-2 px-2 py-1.5 text-sm text-dark-200 hover:bg-dark-800 rounded"
    >
      <span className="w-6 h-6 rounded bg-primary-600 flex items-center justify-center text-white text-xs font-bold">
        {w.name.charAt(0).toUpperCase()}
      </span>
      <span className="truncate flex-1 text-left">{w.name}</span>
      {active && <Check size={14} className="text-primary-400" />}
    </button>
  );
}
