"use client";

import { useState } from "react";
import { useStore } from "@/store";
import { Hash, MessageSquare, Plus } from "lucide-react";
import { sendCreateChannel } from "@/lib/websocket";
import type { Channel } from "@/types";

export function LeftNav() {
  const channels = useStore((s) => s.channels);
  const agents = useStore((s) => s.agents);
  const activeChannel = useStore((s) => s.activeChannel);
  const setActiveChannel = useStore((s) => s.setActiveChannel);
  const collapsedCategories = useStore((s) => s.collapsedCategories);
  const toggleCategory = useStore((s) => s.toggleCategory);
  const threads = useStore((s) => s.threads);
  const project = useStore((s) => s.project);
  const connected = useStore((s) => s.connected);
  const [showCreateChannel, setShowCreateChannel] = useState(false);
  const [newChannelName, setNewChannelName] = useState("");
  const [newChannelParent, setNewChannelParent] = useState("");

  const coworker = agents.find((a) => a.role === "boss" || a.role === "coworker");
  const agentList = agents.filter((a) => a.role !== "boss" && a.role !== "coworker");

  const categories = channels.filter((c) => c.type === "category");
  const uncategorized = channels.filter((c) => !c.parent_id && c.type !== "category");

  const renderChannel = (ch: Channel, depth: number = 0) => (
    <li key={ch.id}>
      <button
        onClick={() => setActiveChannel(ch.id)}
        className={`w-full px-3 py-1.5 rounded-lg text-sm flex items-center gap-2 transition-colors ${
          activeChannel === ch.id
            ? "bg-primary-600/20 text-white"
            : "text-dark-300 hover:bg-dark-700 hover:text-white"
        }`}
        style={{ paddingLeft: `${12 + depth * 16}px` }}
      >
        {ch.type === "category" ? (
          <span className="text-dark-400 text-xs">#</span>
        ) : (
          <Hash className="w-3.5 h-3.5 flex-shrink-0 text-dark-400" />
        )}
        <span className="truncate text-xs">{ch.name}</span>
        {threads.some((t) => t.channel === ch.id) && (
          <span className="ml-auto w-2 h-2 rounded-full bg-primary-500" title="Has active threads" />
        )}
      </button>
      {ch.children && ch.children.length > 0 && (
        <ul className="space-y-0.5">
          {ch.children.map((child) => renderChannel(child, depth + 1))}
        </ul>
      )}
    </li>
  );

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
      <div className="overflow-y-auto p-2 flex-1">
        <div className="flex items-center justify-between mb-2 px-2">
          <span className="text-xs font-semibold text-dark-400 uppercase tracking-wider">Channels</span>
          <button onClick={() => setShowCreateChannel(!showCreateChannel)} className="text-dark-400 hover:text-white p-1 rounded" title="Create channel">
            <Plus className="w-4 h-4" />
          </button>
        </div>

        {showCreateChannel && (
          <div className="px-2 mb-2 space-y-1">
            <input type="text" value={newChannelName} onChange={(e) => setNewChannelName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendCreateChannel(newChannelName, newChannelParent || undefined)}
              placeholder="Channel name" className="w-full px-2 py-1 bg-dark-800 border border-dark-600 rounded text-white text-xs focus:outline-none focus:ring-1 focus:ring-primary-500" autoFocus />
            {categories.length > 0 && (
              <select value={newChannelParent} onChange={(e) => setNewChannelParent(e.target.value)}
                className="w-full px-2 py-1 bg-dark-800 border border-dark-600 rounded text-white text-xs">
                <option value="">No category</option>
                {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            )}
          </div>
        )}

        <ul className="space-y-0.5 mb-4">
          {categories.map((cat) => {
            const isCollapsed = collapsedCategories[cat.id];
            const children = channels.filter((c) => c.parent_id === cat.id);
            return (
              <li key={cat.id}>
                <button
                  onClick={() => toggleCategory(cat.id)}
                  className="w-full px-2 py-1 rounded text-xs font-semibold text-dark-400 hover:text-white flex items-center gap-1"
                >
                  <span className="text-xs">{isCollapsed ? "▶" : "▼"}</span>
                  <span className="uppercase tracking-wider">{cat.name.replace("#", "")}</span>
                </button>
                {!isCollapsed && children.length > 0 && (
                  <ul className="space-y-0.5">
                    {children.map((ch) => renderChannel(ch, 0))}
                  </ul>
                )}
              </li>
            );
          })}

          {uncategorized.map((ch) => renderChannel(ch, 0))}
        </ul>

        {/* Direct Messages */}
        {(coworker || agentList.length > 0) && (
          <>
            <div className="flex items-center justify-between mb-2 px-2">
              <span className="text-xs font-semibold text-dark-400 uppercase tracking-wider">Direct Messages</span>
            </div>
            <ul className="space-y-0.5">
              {coworker && (
                <li>
                  <button
                    onClick={() => setActiveChannel(`dm-${coworker.name.toLowerCase().replace(/\s+/g, "-")}`)}
                    className={`w-full px-3 py-1.5 rounded-lg text-sm flex items-center gap-2 transition-colors ${
                      activeChannel === `dm-${coworker.name.toLowerCase().replace(/\s+/g, "-")}`
                        ? "bg-primary-600/20 text-white" : "text-dark-300 hover:bg-dark-700 hover:text-white"
                    }`}
                  >
                    <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 text-primary-400" />
                    <span className="truncate text-xs">{coworker.display_name || coworker.name}</span>
                  </button>
                </li>
              )}
              {agentList.map((agent) => {
                const dmChannel = `dm-${agent.name.toLowerCase().replace(/\s+/g, "-")}`;
                return (
                  <li key={agent.id}>
                    <button onClick={() => setActiveChannel(dmChannel)}
                      className={`w-full px-3 py-1.5 rounded-lg text-sm flex items-center gap-2 transition-colors ${
                        activeChannel === dmChannel ? "bg-primary-600/20 text-white" : "text-dark-300 hover:bg-dark-700 hover:text-white"
                      }`}>
                      <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 text-dark-400" />
                      <span className="truncate text-xs">{agent.display_name || agent.name}</span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </>
        )}
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