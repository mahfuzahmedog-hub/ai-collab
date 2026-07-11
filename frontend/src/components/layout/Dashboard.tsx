"use client";

import { useState } from "react";
import { useStore } from "@/store";
import {
  Bot,
  CheckCircle2,
  AlertCircle,
  Play,
  TrendingUp,
  Clock,
  Activity,
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
  const logs = useStore((s) => s.executionLogs);
  const audits = useStore((s) => s.lifecycleAudits);
  const [showLifecycle, setShowLifecycle] = useState(false);

  const online = agents.filter((a) => a.status !== "idle" && a.status !== "retired" && a.status !== "archived").length;
  const running = tasks.filter((t) => t.status === "working" || t.status === "planning" || t.status === "assigned").length;
  const completed = tasks.filter((t) => t.status === "completed").length;
  const blocked = tasks.filter((t) => t.status === "blocked").length;

  const vals = { online, running, completed, blocked };

  const totalCost = logs.reduce((s, l) => s + (l.cost_usd || 0), 0);
  const totalTokens = logs.reduce((s, l) => s + (l.total_tokens || 0), 0);
  const avgLatency = logs.length ? Math.round(logs.reduce((s, l) => s + (l.latency_ms || 0), 0) / logs.length) : 0;

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

        {logs.length > 0 && (
          <div className="bg-dark-900/60 border border-dark-700/50 rounded-lg p-3 space-y-2">
            <div className="flex items-center gap-1.5">
              <TrendingUp size={12} className="text-dark-400" />
              <h4 className="text-[10px] font-semibold text-dark-300 uppercase tracking-wider">Observability</h4>
            </div>
            <div className="grid grid-cols-3 gap-2 text-[10px]">
              <div>
                <span className="text-dark-500">Cost</span>
                <p className="text-white font-semibold">${totalCost.toFixed(4)}</p>
              </div>
              <div>
                <span className="text-dark-500">Tokens</span>
                <p className="text-white font-semibold">{totalTokens.toLocaleString()}</p>
              </div>
              <div>
                <span className="text-dark-500">Avg Latency</span>
                <p className="text-white font-semibold">{avgLatency}ms</p>
              </div>
            </div>
            <div className="max-h-24 overflow-y-auto space-y-1">
              {logs.slice(0, 10).map((l) => (
                <div key={l.id} className="flex items-center justify-between text-[10px] text-dark-400">
                  <span className="truncate max-w-[80px]">{l.agent_name}</span>
                  <span className="tabular-nums">{l.total_tokens}t · {l.latency_ms}ms</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="bg-dark-900/60 border border-dark-700/50 rounded-lg">
          <button
            onClick={() => setShowLifecycle(!showLifecycle)}
            className="w-full flex items-center gap-1.5 p-3 text-left"
          >
            <Activity size={12} className="text-dark-400" />
            <h4 className="text-[10px] font-semibold text-dark-300 uppercase tracking-wider">Lifecycle</h4>
            <span className="ml-auto text-dark-500 text-[10px]">{audits.length}</span>
          </button>
          {showLifecycle && (
            <div className="max-h-40 overflow-y-auto px-3 pb-3 space-y-1">
              {audits.slice(0, 30).map((a) => (
                <div key={a.id} className="text-[10px] text-dark-400 border-t border-dark-700/30 pt-1">
                  <span className="text-white">{a.agent_name}</span>
                  <span className="text-dark-500">: {a.from_state} → {a.to_state}</span>
                  {a.reason && <div className="truncate text-dark-500">{a.reason}</div>}
                </div>
              ))}
              {audits.length === 0 && (
                <div className="text-[10px] text-dark-500">No state transitions yet.</div>
              )}
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
