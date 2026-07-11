"use client";

import { useStore } from "@/store";
import { AgentCard } from "@/components/agents/AgentCard";

export function AgentsPage() {
  const agents = useStore((s) => s.agents);

  const boss = agents.find((a) => a.role === "boss" || a.role === "coworker");
  const workers = agents.filter((a) => a.role !== "boss" && a.role !== "coworker");

  return (
    <div className="h-full overflow-y-auto scrollbar-thin p-4">
      {agents.length === 0 ? (
        <div className="flex items-center justify-center h-64 text-dark-500">
          <div className="text-center">
            <div className="text-4xl mb-3">🤝</div>
            <p className="text-lg text-white font-semibold mb-2">No agents yet</p>
            <p className="text-sm text-dark-400">Your Coworker will build a team when you start a project.</p>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {boss && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <h2 className="text-lg font-bold text-primary-400">Coworker</h2>
                <div className="h-px flex-1 bg-gradient-to-r from-primary-500/20 to-transparent" />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                <AgentCard key={boss.id} agent={boss} />
              </div>
            </div>
          )}

          <div>
            <div className="flex items-center gap-2 mb-3">
              <h2 className="text-lg font-bold text-white">Team Members</h2>
              <span className="text-xs bg-dark-700 text-dark-300 px-2 py-0.5 rounded-full">{workers.length}</span>
              <div className="h-px flex-1 bg-gradient-to-r from-dark-700 to-transparent" />
            </div>
            {workers.length === 0 ? (
              <p className="text-sm text-dark-500 py-8 text-center">No team members yet. Your Coworker will build a team for your project.</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                {workers.map((agent) => (
                  <AgentCard key={agent.id} agent={agent} />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
