"use client";

import { useStore } from "@/store";
import { clsx } from "clsx";
import { Bell, Search, TrendingUp, Users, Settings } from "lucide-react";
import { SettingsPanel } from "@/features/settings/SettingsPanel";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

const TAB_LABELS: Record<string, string> = {
  chat: "Chat",
  tasks: "Tasks",
  agents: "Agents",
  files: "Files",
  activity: "Activity",
};

export function WorkspaceHeader() {
  const project = useStore((s) => s.project);
  const connected = useStore((s) => s.connected);
  const agents = useStore((s) => s.agents);
  const setCommandPaletteOpen = useStore((s) => s.setCommandPaletteOpen);
  const setNotificationsOpen = useStore((s) => s.setNotificationsOpen);
  const setSettingsPanelOpen = useStore((s) => s.setSettingsPanelOpen);
  const zenConnected = useStore((s) => s.zenConnected);
  const unreadNotifs = useStore((s) => s.notifications.filter((n) => !n.read).length);

  // ?tab= is the single source of truth for the active tab
  const searchParams = useSearchParams();
  const activeTab = searchParams.get("tab") || "chat";
  const tabLabel = TAB_LABELS[activeTab] || activeTab;
  const activeAgents = agents.filter(
    (a) => a.status !== "idle" && a.status !== "retired"
  ).length;

  return (
    <header className="h-12 flex-shrink-0 border-b border-dark-700 bg-dark-950 flex items-center px-4 gap-3 z-20">
      <span className="text-sm font-semibold text-white truncate min-w-0">
        {project?.title || "Workspace"}
      </span>
      <span className="text-dark-600">/</span>
      <span className="text-sm text-dark-300 capitalize">{tabLabel}</span>

      <div className="flex items-center gap-1.5 ml-2">
        <span
          className={clsx(
            "w-1.5 h-1.5 rounded-full",
            connected ? "bg-green-500 pulse-working" : "bg-red-500"
          )}
        />
        <span className="text-[10px] text-dark-400 font-medium">
          {connected ? "Live" : "Offline"}
        </span>
        <span
          className={clsx(
            "w-1.5 h-1.5 rounded-full",
            zenConnected ? "bg-green-500" : "bg-dark-600"
          )}
          title={zenConnected ? "Zen API connected" : "Zen API not configured"}
        />
      </div>

      <div className="flex-1" />

      <button
        onClick={() => setCommandPaletteOpen(true)}
        className="flex items-center gap-1.5 bg-dark-800 border border-dark-700 rounded-md px-2.5 py-1.5 text-dark-400 hover:text-white transition-colors text-xs"
      >
        <Search size={14} /> Search
        <span className="text-[10px] text-dark-600 bg-dark-700 px-1 rounded">
          Ctrl+K
        </span>
      </button>

      <div
        className="flex items-center gap-1.5 text-dark-400 text-xs border border-dark-700 rounded-md px-2 py-1.5"
        title="Presence"
      >
        <Users size={14} /> {activeAgents} active
      </div>

      <button
        onClick={() => setSettingsPanelOpen(true)}
        className="text-dark-400 hover:text-dark-200 transition-colors"
        title="LLM Settings"
      >
        <Settings size={16} />
      </button>
      <button
        onClick={() => setNotificationsOpen(true)}
        className="text-dark-400 hover:text-dark-200 transition-colors relative"
        title="Notifications"
      >
        <Bell size={16} />
        {unreadNotifs > 0 && (
          <span className="absolute -top-1.5 -right-1.5 bg-accent-500 text-white text-[9px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
            {unreadNotifs > 9 ? "9+" : unreadNotifs}
          </span>
        )}
      </button>

      <Link
        href="/dashboard"
        className="text-dark-400 hover:text-dark-200 transition-colors"
        title="Dashboard"
      >
        <TrendingUp size={16} />
      </Link>
      <SettingsPanel />
    </header>
  );
}
