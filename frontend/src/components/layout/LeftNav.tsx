"use client";

import { useStore } from "@/store";
import { clsx } from "clsx";
import {
  Activity,
  Bot,
  CheckSquare,
  Layers,
  LayoutDashboard,
} from "lucide-react";

const tabs = [
  { id: "workspace", label: "Activity", icon: Activity },
  { id: "agents", label: "Agents", icon: Bot },
  { id: "tasks", label: "Tasks", icon: CheckSquare },
];

const bossStatusColor: Record<string, string> = {
  idle: "bg-dark-500",
  thinking: "bg-yellow-400 animate-pulse",
  working: "bg-green-500 pulse-working",
  waiting: "bg-blue-500",
  blocked: "bg-red-500",
  reviewing: "bg-purple-500",
  testing: "bg-orange-500",
  done: "bg-emerald-500",
};

export function LeftNav() {
  const activeTab = useStore((s) => s.activeTab);
  const setActiveTab = useStore((s) => s.setActiveTab);
  const agents = useStore((s) => s.agents);
  const tasks = useStore((s) => s.tasks);
  const connected = useStore((s) => s.connected);

  const boss = agents.find((a) => a.role === "boss");
  const workerCount = agents.filter((a) => a.role !== "boss").length;

  return (
    <nav className="w-56 bg-dark-900 border-r border-dark-700/60 flex flex-col h-full shrink-0 z-10">
      <div className="px-4 py-3 border-b border-dark-700/60">
        <div className="flex items-center gap-2">
          <Layers size={16} className="text-accent-400" />
          <h2 className="text-sm font-bold text-white tracking-wide">AI Collab</h2>
        </div>
      </div>

      {boss && (
        <div className="mx-2.5 mt-2.5 mb-1 p-2.5 rounded-lg bg-accent-500/5 border border-accent-500/15">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-accent-500/15 flex items-center justify-center shrink-0 ring-1 ring-accent-500/30">
              <LayoutDashboard size={14} className="text-accent-400" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-semibold text-accent-300 truncate">{boss.name}</span>
                <div className={clsx("w-1.5 h-1.5 rounded-full shrink-0", bossStatusColor[boss.status] || "bg-dark-500")} />
              </div>
              <p className="text-[10px] text-dark-400 truncate">Engineering Manager</p>
            </div>
          </div>
          <div className="mt-1.5 flex gap-2.5 text-[10px] text-dark-500">
            <span className="text-dark-400">{workerCount} agent{workerCount !== 1 ? "s" : ""}</span>
            <span className="text-dark-400">{tasks.length} task{tasks.length !== 1 ? "s" : ""}</span>
          </div>
        </div>
      )}

      <div className="flex-1 py-2">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                "w-full flex items-center gap-2.5 px-4 py-2 text-sm transition-colors",
                activeTab === tab.id
                  ? "bg-accent-600/10 text-accent-400 border-r-2 border-accent-500"
                  : "text-dark-300 hover:text-white hover:bg-dark-800/50"
              )}
            >
              <Icon size={15} />
              <span>{tab.label}</span>
              {tab.id === "agents" && agents.length > 0 && (
                <span className="ml-auto text-[10px] bg-dark-700 text-dark-400 px-1.5 py-0.5 rounded-full leading-none">
                  {agents.length}
                </span>
              )}
              {tab.id === "tasks" && tasks.length > 0 && (
                <span className="ml-auto text-[10px] bg-dark-700 text-dark-400 px-1.5 py-0.5 rounded-full leading-none">
                  {tasks.length}
                </span>
              )}
              {tab.id === "workspace" && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-accent-500/60" />
              )}
            </button>
          );
        })}
      </div>

      <div className="px-4 py-2.5 border-t border-dark-700/60">
        <div className="flex items-center gap-1.5 mb-0.5">
          <div className={clsx("w-1.5 h-1.5 rounded-full", connected ? "bg-green-500" : "bg-red-500")} />
          <span className="text-[10px] text-dark-500">{connected ? "Connected" : "Offline"}</span>
        </div>
        <p className="text-[10px] text-dark-600">AI Collab v0.1</p>
      </div>
    </nav>
  );
}
