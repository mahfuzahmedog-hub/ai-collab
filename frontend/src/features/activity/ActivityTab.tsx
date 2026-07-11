"use client";

import { useStore } from "@/store";
import { TrendingUp, DollarSign, Activity, Clock } from "lucide-react";

// M6: dashboard parity inside the persistent workspace shell (Activity tab).
export function ActivityTab() {
  const agents = useStore((s) => s.agents);
  const logs = useStore((s) => s.executionLogs);
  const audits = useStore((s) => s.lifecycleAudits);

  const totalCost = logs.reduce((s, l) => s + (l.cost_usd || 0), 0);
  const totalTokens = logs.reduce((s, l) => s + (l.total_tokens || 0), 0);
  const avgLatency = logs.length
    ? Math.round(logs.reduce((s, l) => s + (l.latency_ms || 0), 0) / logs.length)
    : 0;
  const activeAgents = agents.filter(
    (a) => !["idle", "retired", "completed", "archived", "paused"].includes(a.status)
  ).length;

  const stats = [
    { label: "Active Agents", value: activeAgents, icon: TrendingUp, color: "text-blue-400" },
    { label: "Total Cost", value: `$${totalCost.toFixed(4)}`, icon: DollarSign, color: "text-green-400" },
    { label: "Total Tokens", value: totalTokens.toLocaleString(), icon: Activity, color: "text-purple-400" },
    { label: "Avg Latency", value: `${avgLatency}ms`, icon: Clock, color: "text-yellow-400" },
  ];

  return (
    <div className="h-full overflow-y-auto scrollbar-thin p-4 bg-dark-950 space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s) => {
          const Icon = s.icon;
          return (
            <div key={s.label} className="bg-dark-900 rounded-lg p-4 border border-dark-700">
              <div className="flex items-center gap-2 mb-2">
                <Icon size={16} className={s.color} />
                <span className="text-xs text-dark-400">{s.label}</span>
              </div>
              <span className="text-2xl font-bold text-white">{s.value}</span>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-dark-900 rounded-lg p-4 border border-dark-700">
          <h2 className="font-semibold mb-3 flex items-center gap-2 text-white">
            <Activity size={16} /> Lifecycle Events
          </h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {audits.slice(0, 50).map((a) => (
              <div key={a.id} className="text-xs bg-dark-800 p-2 rounded flex items-center justify-between">
                <span className="text-dark-200">{a.agent_name}: {a.from_state} → {a.to_state}</span>
                <span className="text-dark-500">{a.reason}</span>
              </div>
            ))}
            {audits.length === 0 && <div className="text-xs text-dark-500">No lifecycle events yet.</div>}
          </div>
        </div>

        <div className="bg-dark-900 rounded-lg p-4 border border-dark-700">
          <h2 className="font-semibold mb-3 flex items-center gap-2 text-white">
            <Activity size={16} /> Execution Logs
          </h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {logs.slice(0, 50).map((l) => (
              <div key={l.id} className="text-xs bg-dark-800 p-2 rounded">
                <div className="flex justify-between">
                  <span className="text-dark-200">{l.agent_name}</span>
                  <span className="text-dark-500">{l.model}</span>
                </div>
                <div className="text-dark-500">
                  {l.total_tokens}t · ${l.cost_usd?.toFixed(6)} · {l.latency_ms}ms
                </div>
              </div>
            ))}
            {logs.length === 0 && <div className="text-xs text-dark-500">No execution logs yet.</div>}
          </div>
        </div>
      </div>

      <div className="bg-dark-900 rounded-lg p-4 border border-dark-700">
        <h2 className="font-semibold mb-3 text-white">Agents</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-dark-400 text-xs uppercase">
                <th className="text-left p-2">Name</th>
                <th className="text-left p-2">Status</th>
                <th className="text-left p-2">Role</th>
                <th className="text-left p-2">Task</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((a) => (
                <tr key={a.id} className="border-t border-dark-700">
                  <td className="p-2 text-white">{a.display_name || a.name}</td>
                  <td className="p-2"><span className="px-2 py-0.5 rounded bg-dark-700 text-xs text-dark-200">{a.status}</span></td>
                  <td className="p-2 text-dark-400">{a.role}</td>
                  <td className="p-2 text-dark-400">{a.current_task_id || "—"}</td>
                </tr>
              ))}
              {agents.length === 0 && (
                <tr><td colSpan={4} className="p-2 text-dark-500 text-xs">No agents yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
