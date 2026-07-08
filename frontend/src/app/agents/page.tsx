"use client";

import { useStore } from "@/store";
import { AgentCard } from "@/components/agents/AgentCard";

export function AgentsPage() {
  const agents = useStore((s) => s.agents);

  return (
    <div className="h-full overflow-y-auto scrollbar-thin p-4">
      <div className="mb-4">
        <h2 className="text-lg font-bold text-white">Team Members</h2>
        <p className="text-sm text-dark-400">{agents.length} agent{(agents.length || 1) > 1 ? "s" : ""} active</p>
      </div>

      {agents.length === 0 ? (
        <div className="flex items-center justify-center h-64 text-dark-500">
          <div className="text-center">
            <p className="text-lg mb-2">No agents yet</p>
            <p className="text-sm">The Boss Agent will create team members when you submit a project.</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {agents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      )}
    </div>
  );
}
