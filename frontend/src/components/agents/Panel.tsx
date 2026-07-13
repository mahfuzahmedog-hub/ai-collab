"use client";

import { useState } from "react";
import { useStore } from "@/store";
import { AgentCard } from "@/components/agents/AgentCard";
import { sendCommand } from "@/lib/websocket";
import { Plus, X } from "lucide-react";

export function AgentsPage() {
  const agents = useStore((s) => s.agents);
  const [showForm, setShowForm] = useState(false);
  const [newName, setNewName] = useState("");
  const [newRole, setNewRole] = useState("");

  const boss = agents.find((a) => a.role === "boss" || a.role === "coworker");
  const workers = agents.filter((a) => a.role !== "boss" && a.role !== "coworker");

  const handleCreate = () => {
    if (!newName.trim()) return;
    sendCommand("add_agent", { name: newName.trim(), role: newRole.trim() || "engineer" });
    setNewName("");
    setNewRole("");
    setShowForm(false);
  };

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
              <button
                onClick={() => setShowForm(true)}
                className="flex items-center gap-1 text-xs bg-dark-800 hover:bg-dark-700 border border-dark-700 text-dark-200 px-2 py-1 rounded transition-colors"
              >
                <Plus size={12} /> New Agent
              </button>
            </div>

            {showForm && (
              <div className="mb-4 p-3 bg-dark-800 border border-dark-700 rounded-lg flex items-center gap-2">
                <input
                  autoFocus
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                  placeholder="Agent name"
                  className="flex-1 bg-dark-900 border border-dark-600 rounded px-2 py-1.5 text-white text-sm placeholder-dark-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
                <input
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                  placeholder="Role (e.g. engineer)"
                  className="w-36 bg-dark-900 border border-dark-600 rounded px-2 py-1.5 text-white text-sm placeholder-dark-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
                <button onClick={handleCreate} disabled={!newName.trim()} className="bg-primary-600 hover:bg-primary-500 disabled:opacity-50 text-white text-xs px-3 py-1.5 rounded transition-colors">Create</button>
                <button onClick={() => setShowForm(false)} className="text-dark-400 hover:text-white p-1"><X size={14} /></button>
              </div>
            )}

            {workers.length === 0 && !showForm ? (
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
