"use client";

import { useStore } from "@/store";
import {
  Bot,
  CheckCircle2,
  AlertCircle,
  Play,
  TrendingUp,
  Clock,
} from "lucide-react";

const cards = [
  { label: "Online", key: "online", icon: Bot, color: "text-green-400" },
  { label: "Running", key: "running", icon: Play, color: "text-blue-400" },
  { label: "Completed", key: "completed", icon: CheckCircle2, color: "text-emerald-400" },
  { label: "Blocked", key: "blocked", icon: AlertCircle, color: "text-red-400" },
];

export function Dashboard() {
  const agents = useStore((s) => s.agents);
  const tasks = useStore((s) => s.tasks);

  const online = agents.filter((a) => a.status !== "idle" && a.status !== "done").length;
  const running = tasks.filter((t) => t.status === "working" || t.status === "planning" || t.status === "assigned").length;
  const completed = tasks.filter((t) => t.status === "completed").length;
  const blocked = tasks.filter((t) => t.status === "blocked").length;

  const vals = { online, running, completed, blocked };

  if (agents.length === 0) return null;

  return (
    <aside className="w-60 bg-dark-950/30 border-l border-dark-700/40 flex flex-col h-full shrink-0 overflow-hidden">
      <div className="px-3 py-2.5 border-b border-dark-700/40 shrink-0">
        <div className="flex items-center gap-2">
          <TrendingUp size={14} className="text-dark-400" />
          <h3 className="text-xs font-semibold text-dark-200 uppercase tracking-wider">Mission</h3>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin p-3 space-y-2.5">
        <div className="grid grid-cols-2 gap-2">
          {cards.map((c) => {
            const Icon = c.icon;
            return (
              <div key={c.key} className="bg-dark-900/60 border border-dark-700/50 rounded-lg p-2.5">
                <div className="flex items-center gap-1.5 mb-1">
                  <Icon size={12} className={c.color} />
                  <span className="text-[10px] text-dark-500">{c.label}</span>
                </div>
                <span className="text-lg font-bold text-white tabular-nums">
                  {vals[c.key as keyof typeof vals]}
                </span>
              </div>
            );
          })}
        </div>

        {agents.length > 0 && (
          <div className="bg-dark-900/60 border border-dark-700/50 rounded-lg p-3">
            <div className="flex items-center gap-1.5 mb-2">
              <Clock size={12} className="text-dark-400" />
              <h4 className="text-[10px] font-semibold text-dark-300 uppercase tracking-wider">Recent Activity</h4>
            </div>
            <p className="text-[10px] text-dark-500 leading-relaxed">
              {agents.filter(a => a.status === "thinking" || a.status === "working").length > 0
                ? `${agents.filter(a => a.status === "thinking" || a.status === "working").length} agent(s) currently active`
                : "All agents idle"}
            </p>
          </div>
        )}
      </div>
    </aside>
  );
}
