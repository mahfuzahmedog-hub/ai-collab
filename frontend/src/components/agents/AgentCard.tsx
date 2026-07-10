import type { Agent } from "@/types";
import { clsx } from "clsx";

const statusColors: Record<string, string> = {
  idle: "bg-dark-500",
  thinking: "bg-yellow-500 animate-pulse",
  working: "bg-green-500",
  waiting: "bg-blue-500",
  blocked: "bg-red-500",
  reviewing: "bg-purple-500",
  testing: "bg-orange-500",
  done: "bg-emerald-500",
};

const roleIcons: Record<string, string> = {
  boss: "👑",
  planner: "📋",
  researcher: "🔍",
  architect: "🏗️",
  backend_engineer: "⚙️",
  frontend_engineer: "🎨",
  reviewer: "👁️",
  qa_engineer: "🧪",
  devops: "🚀",
  security_engineer: "🔒",
  database_engineer: "🗄️",
  documentation_writer: "📝",
};

export function AgentCard({ agent }: { agent: Agent }) {
  const isBoss = agent.role === "boss" || agent.role === "coworker";

  if (isBoss) {
    return (
      <div className="bg-gradient-to-br from-yellow-500/5 to-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 hover:border-yellow-500/50 transition-all col-span-full sm:col-span-2 lg:col-span-1">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-yellow-500/20 flex items-center justify-center text-2xl shrink-0 ring-2 ring-yellow-500/30">
            👑
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-yellow-400 truncate">{agent.name}</h3>
              <div className={clsx("w-2.5 h-2.5 rounded-full shrink-0", statusColors[agent.status] || "bg-dark-500")} />
            </div>
            <p className="text-xs text-yellow-500/80">Engineering Manager</p>
          </div>
        </div>

        <div className="mt-3 flex flex-wrap gap-1.5">
          <span className="text-xs bg-yellow-500/10 text-yellow-400 px-2 py-0.5 rounded-full font-medium">Team Lead</span>
          {agent.skills.slice(0, 3).map((skill) => (
            <span key={skill} className="text-xs bg-dark-700 text-dark-300 px-1.5 py-0.5 rounded">
              {skill}
            </span>
          ))}
        </div>

        {agent.status === "thinking" && (
          <div className="mt-3 flex gap-1">
            <span className="thinking-dot w-1.5 h-1.5 bg-yellow-400 rounded-full" />
            <span className="thinking-dot w-1.5 h-1.5 bg-yellow-400 rounded-full" />
            <span className="thinking-dot w-1.5 h-1.5 bg-yellow-400 rounded-full" />
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="bg-dark-800 border border-dark-700 rounded-lg p-3 hover:border-dark-500 transition-colors">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-dark-700 flex items-center justify-center text-lg">
          {roleIcons[agent.role] || "🤖"}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-white truncate">{agent.name}</h3>
            <div className={clsx("w-2 h-2 rounded-full shrink-0", statusColors[agent.status] || "bg-dark-500")} />
          </div>
          <p className="text-xs text-dark-400 capitalize truncate">
            {agent.role.replace(/_/g, " ")}
          </p>
        </div>
      </div>

      {agent.current_task_id && (
        <div className="mt-2 text-xs text-dark-300 truncate">
          Task: {agent.current_task_id}
        </div>
      )}

      {agent.skills.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {agent.skills.slice(0, 3).map((skill) => (
            <span key={skill} className="text-xs bg-dark-700 text-dark-300 px-1.5 py-0.5 rounded">
              {skill}
            </span>
          ))}
        </div>
      )}

      {agent.status === "thinking" && (
        <div className="mt-2 flex gap-1">
          <span className="thinking-dot w-1.5 h-1.5 bg-yellow-400 rounded-full" />
          <span className="thinking-dot w-1.5 h-1.5 bg-yellow-400 rounded-full" />
          <span className="thinking-dot w-1.5 h-1.5 bg-yellow-400 rounded-full" />
        </div>
      )}
    </div>
  );
}
