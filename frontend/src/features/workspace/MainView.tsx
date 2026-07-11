"use client";

import { useStore } from "@/store";
import { Timeline } from "@/components/timeline/Timeline";
import { TasksPage } from "@/components/tasks/Panel";
import { AgentsPage } from "@/components/agents/Panel";
import { Activity, Code } from "lucide-react";

export function MainView({ tab }: { tab: string }) {
  switch (tab) {
    case "tasks":
      return <TasksPage />;
    case "agents":
      return <AgentsPage />;
    case "files":
      return (
        <div className="h-full flex items-center justify-center text-dark-500 bg-dark-950">
          <div className="text-center">
            <Code className="w-8 h-8 mx-auto mb-2" />
            <p className="text-sm">Files (M2)</p>
          </div>
        </div>
      );
    case "activity":
      return <ActivityPanel />;
    case "chat":
    default:
      return <Timeline />;
  }
}

// Mirror of app/dashboard/page.tsx ops view: execution logs + lifecycle audits.
function ActivityPanel() {
  const logs = useStore((s) => s.executionLogs);
  const audits = useStore((s) => s.lifecycleAudits);

  return (
    <div className="h-full overflow-y-auto scrollbar-thin p-4 bg-dark-950 space-y-4">
      <div className="bg-dark-900 rounded-lg p-4 border border-dark-700">
        <h2 className="font-semibold mb-3 flex items-center gap-2 text-white">
          <Activity size={16} /> Lifecycle Events
        </h2>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {audits.slice(0, 50).map((a) => (
            <div
              key={a.id}
              className="text-xs bg-dark-800 p-2 rounded flex items-center justify-between"
            >
              <span>
                {a.agent_name}: {a.from_state} → {a.to_state}
              </span>
              <span className="text-dark-500">{a.reason}</span>
            </div>
          ))}
          {audits.length === 0 && (
            <div className="text-xs text-dark-500">No lifecycle events yet.</div>
          )}
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
                <span>{l.agent_name}</span>
                <span className="text-dark-500">{l.model}</span>
              </div>
              <div className="text-dark-500">
                {l.total_tokens}t · ${l.cost_usd?.toFixed(6)} · {l.latency_ms}ms
              </div>
            </div>
          ))}
          {logs.length === 0 && (
            <div className="text-xs text-dark-500">No execution logs yet.</div>
          )}
        </div>
      </div>
    </div>
  );
}
