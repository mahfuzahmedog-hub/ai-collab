"use client";

import { useStore } from "@/store";
import { clsx } from "clsx";
import { Bot, Cpu, Clock } from "lucide-react";

const statusColors: Record<string, string> = {
  idle: "bg-dark-500",
  thinking: "bg-yellow-400 animate-pulse",
  working: "bg-green-500 pulse-working",
  waiting: "bg-blue-500",
  blocked: "bg-red-500",
  reviewing: "bg-purple-500",
  testing: "bg-orange-500",
  done: "bg-emerald-500",
};

const roleIcons: Record<string, string> = {
  boss: "👑", planner: "📋", researcher: "🔍", architect: "🏗️",
  backend_engineer: "⚙️", frontend_engineer: "🎨", reviewer: "👁️",
  qa_engineer: "🧪", devops: "🚀", security_engineer: "🔒",
  database_engineer: "🗄️", documentation_writer: "📝",
};

export function AgentSidebar() {
  const agents = useStore((s) => s.agents);
  const boss = agents.find((a) => a.role === "boss");
  const workers = agents.filter((a) => a.role !== "boss");

  if (agents.length === 0) return null;

  return (
    <aside className="w-64 bg-dark-900/50 border-l border-dark-700/40 flex flex-col h-full shrink-0 overflow-hidden">
      <div className="px-3 py-2.5 border-b border-dark-700/40 flex items-center gap-2 shrink-0">
        <Bot size={14} className="text-dark-400" />
        <h3 className="text-xs font-semibold text-dark-200 uppercase tracking-wider">Agents</h3>
        <span className="ml-auto text-[10px] bg-dark-700 text-dark-400 px-1.5 py-0.5 rounded-full leading-none">
          {workers.length}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin py-1.5 space-y-0.5">
        {boss && <AgentRow agent={boss} isBoss />}
        {workers.map((agent) => (
          <AgentRow key={agent.id} agent={agent} />
        ))}
      </div>
    </aside>
  );
}

function AgentRow({ agent, isBoss = false }: { agent: any; isBoss?: boolean }) {
  const isThinking = agent.status === "thinking";
  const isWorking = agent.status === "working";

  return (
    <div
      className={clsx(
        "mx-1.5 px-2.5 py-2 rounded-md transition-colors",
        isBoss
          ? "bg-accent-500/5 border border-accent-500/10"
          : "hover:bg-dark-800/50"
      )}
    >
      <div className="flex items-center gap-2.5">
        <div className="relative shrink-0">
          <div className={clsx(
            "w-8 h-8 rounded-full flex items-center justify-center text-sm",
            isBoss ? "bg-accent-500/15" : "bg-dark-700"
          )}>
            {roleIcons[agent.role] || "🤖"}
          </div>
          <div className={clsx(
            "absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-dark-900",
            statusColors[agent.status] || "bg-dark-500"
          )} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <span className={clsx(
              "text-xs font-semibold truncate",
              isBoss ? "text-accent-300" : "text-dark-100"
            )}>
              {agent.name}
            </span>
            {(isThinking || isWorking) && (
              <span className="w-1 h-1 rounded-full bg-yellow-400 animate-pulse shrink-0" />
            )}
          </div>
          <p className="text-[10px] text-dark-500 truncate capitalize">
            {agent.role.replace(/_/g, " ")}
          </p>
        </div>
      </div>

      <div className="mt-1.5 flex items-center gap-2 text-[10px] text-dark-500">
        {agent.current_task_id ? (
          <span className="truncate text-dark-400 max-w-[140px]">
            {agent.current_task_id}
          </span>
        ) : (
          <span className="text-dark-600">Idle</span>
        )}
        {isBoss && (
          <>
            <Cpu size={10} className="shrink-0" />
            <span className="shrink-0">{agent.provider || "default"}</span>
          </>
        )}
      </div>

      {agent.skills && agent.skills.length > 0 && (
        <div className="mt-1 flex gap-1 flex-wrap">
          {agent.skills.slice(0, 2).map((s: string) => (
            <span key={s} className="text-[9px] bg-dark-700 text-dark-400 px-1 py-0.5 rounded">
              {s}
            </span>
          ))}
          {agent.skills.length > 2 && (
            <span className="text-[9px] text-dark-600">+{agent.skills.length - 2}</span>
          )}
        </div>
      )}
    </div>
  );
}
