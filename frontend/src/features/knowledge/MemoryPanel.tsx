"use client";

import { useState } from "react";
import { useStore } from "@/store";
import { Search, Database, Clock, Tag } from "lucide-react";

export function MemoryPanel() {
  const memories = useStore((s) => s.memories);
  const [filter, setFilter] = useState<string>("all");
  const [search, setSearch] = useState("");

  const filtered = memories.filter((m) => {
    if (filter !== "all" && m.type !== filter) return false;
    if (search && !m.content.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const types = ["all", ...new Set(memories.map((m) => m.type))];

  return (
    <div className="flex flex-col h-full bg-dark-950">
      <div className="px-4 py-3 border-b border-dark-700 bg-dark-900">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Database className="w-4 h-4 text-primary-400" />
          Memory Store
        </h2>
        <div className="flex gap-2 mt-2">
          <div className="relative flex-1">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-dark-500" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search memories..."
              className="w-full bg-dark-800 border border-dark-600 rounded pl-7 pr-2 py-1.5 text-xs text-white placeholder-dark-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            />
          </div>
        </div>
        <div className="flex gap-1 mt-2 flex-wrap">
          {types.map((t) => (
            <button
              key={t}
              onClick={() => setFilter(t)}
              className={`text-[10px] px-2 py-0.5 rounded-full ${
                filter === t ? "bg-primary-600 text-white" : "bg-dark-800 text-dark-400 hover:text-dark-200"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {filtered.length === 0 && (
          <div className="text-dark-500 text-xs text-center py-8">No memories found</div>
        )}
        {filtered.slice(0, 100).map((m) => (
          <div key={m.id} className="border border-dark-700 rounded-lg p-3 bg-dark-900/50">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] uppercase text-primary-400 bg-primary-600/20 px-1.5 py-0.5 rounded">{m.type}</span>
              <span className="text-[10px] text-dark-500 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {new Date(m.created_at).toLocaleDateString()}
              </span>
              {m.tags?.length > 0 && (
                <span className="text-[10px] text-dark-500 flex items-center gap-1">
                  <Tag className="w-3 h-3" />
                  {m.tags.slice(0, 3).join(", ")}
                </span>
              )}
            </div>
            <p className="text-xs text-dark-200 line-clamp-3">{m.content}</p>
            <div className="mt-1 flex items-center gap-2">
              <div className="h-1 flex-1 bg-dark-700 rounded-full overflow-hidden">
                <div className="h-full bg-primary-500 rounded-full" style={{ width: `${m.importance * 100}%` }} />
              </div>
              <span className="text-[10px] text-dark-500">{Math.round(m.importance * 100)}%</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
