"use client";

import { useState } from "react";
import { useStore } from "@/store";
import { Hash, MessageSquare, Users, CheckSquare, Plus } from "lucide-react";

export function LeftNav() {
  const channels = useStore((s) => s.channels);
  const activeChannel = useStore((s) => s.activeChannel);
  const setActiveChannel = useStore((s) => s.setActiveChannel);
  const activeProjectId = useStore((s) => s.activeProjectId);
  const project = useStore((s) => s.project);
  const connected = useStore((s) => s.connected);
  const [showCreateChannel, setShowCreateChannel] = useState(false);
  const [newChannelName, setNewChannelName] = useState("");

  const handleCreateChannel = () => {
    if (!newChannelName.trim() || !activeProjectId) return;
    const channel = {
      id: newChannelName.toLowerCase().replace(/[^a-z0-9]/g, "-"),
      name: `#${newChannelName}`,
      project_id: activeProjectId,
      unread: false,
    };
    setActiveChannel(channel.id);
    useStore.getState().addChannel(channel);
    setShowCreateChannel(false);
    setNewChannelName("");
  };

  return (
    <aside className="w-56 flex-shrink-0 bg-dark-900 border-r border-dark-700 flex flex-col h-full">
      {/* Project header */}
      <div className="p-4 border-b border-dark-700">
        <div className="flex items-center gap-2 mb-3">
          <Hash className="w-5 h-5 text-primary-400" />
          <span className="font-semibold text-white">AI Collab</span>
        </div>
        {project && (
          <div className="text-xs text-dark-400 truncate">{project.title}</div>
        )}
      </div>

      {/* Channels */}
      <div className="flex-1 overflow-y-auto p-2">
        <div className="flex items-center justify-between mb-2 px-2">
          <span className="text-xs font-semibold text-dark-400 uppercase tracking-wider">
            Channels
          </span>
          <button
            onClick={() => setShowCreateChannel(true)}
            className="text-dark-400 hover:text-white p-1 rounded"
            title="Create channel"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>

        {showCreateChannel && (
          <div className="px-2 mb-2">
            <input
              type="text"
              value={newChannelName}
              onChange={(e) => setNewChannelName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreateChannel()}
              placeholder="Channel name"
              className="w-full px-2 py-1.5 bg-dark-800 border border-dark-600 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
              autoFocus
            />
          </div>
        )}

        <ul className="space-y-1">
          {channels.map((ch) => (
            <li key={ch.id}>
              <button
                onClick={() => setActiveChannel(ch.id)}
                className={`w-full px-3 py-2 rounded-lg text-sm flex items-center gap-2 transition-colors ${
                  activeChannel === ch.id
                    ? "bg-primary-600/20 text-white"
                    : "text-dark-300 hover:bg-dark-700 hover:text-white"
                }`}
              >
                <Hash className="w-4 h-4 flex-shrink-0" />
                <span className="truncate">{ch.name}</span>
                {ch.unread && (
                  <span className="ml-auto w-1.5 h-1.5 rounded-full bg-red-500" />
                )}
              </button>
            </li>
          ))}
        </ul>
      </div>

      {/* Connection status */}
      <div className="p-3 border-t border-dark-700">
        <div className="flex items-center gap-2 text-xs text-dark-400">
          <span
            className={`w-2 h-2 rounded-full ${
              connected ? "bg-green-500" : "bg-red-500"
            }`}
          />
          <span>{connected ? "Connected" : "Disconnected"}</span>
        </div>
        <div className="text-xs text-dark-500 mt-1">v0.2.0</div>
      </div>
    </aside>
  );
}