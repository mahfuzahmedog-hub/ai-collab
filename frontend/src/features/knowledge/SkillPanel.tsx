"use client";

import { useState } from "react";
import { useStore } from "@/store";
import { Search, BookOpen, Zap, BarChart3 } from "lucide-react";

export function SkillPanel() {
  const skills = useStore((s) => s.skills);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<string>("all");

  const filtered = skills.filter((s) => {
    if (category !== "all" && s.category !== category) return false;
    if (search && !s.name.toLowerCase().includes(search.toLowerCase()) && !s.description.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const categories = ["all", ...new Set(skills.map((s) => s.category))];

  return (
    <div className="flex flex-col h-full bg-dark-950">
      <div className="px-4 py-3 border-b border-dark-700 bg-dark-900">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-primary-400" />
          Skill Library
        </h2>
        <div className="relative mt-2">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-dark-500" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search skills..."
            className="w-full bg-dark-800 border border-dark-600 rounded pl-7 pr-2 py-1.5 text-xs text-white placeholder-dark-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          />
        </div>
        <div className="flex gap-1 mt-2 flex-wrap">
          {categories.map((c) => (
            <button
              key={c}
              onClick={() => setCategory(c)}
              className={`text-[10px] px-2 py-0.5 rounded-full ${
                category === c ? "bg-primary-600 text-white" : "bg-dark-800 text-dark-400 hover:text-dark-200"
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {filtered.length === 0 && (
          <div className="text-dark-500 text-xs text-center py-8">No skills registered yet</div>
        )}
        {filtered.map((s) => (
          <div key={s.id} className="border border-dark-700 rounded-lg p-3 bg-dark-900/50">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-white">{s.name}</span>
              <span className="text-[10px] uppercase text-dark-400 bg-dark-800 px-1.5 py-0.5 rounded">{s.category}</span>
            </div>
            <p className="text-xs text-dark-400 mb-2">{s.description}</p>
            {s.trigger_phrases?.length > 0 && (
              <div className="flex gap-1 flex-wrap mb-2">
                {s.trigger_phrases.map((p) => (
                  <span key={p} className="text-[10px] text-dark-500 bg-dark-800 px-1.5 py-0.5 rounded">{p}</span>
                ))}
              </div>
            )}
            <div className="flex items-center gap-3 text-[10px] text-dark-500">
              <span className="flex items-center gap-1">
                <Zap className="w-3 h-3" />
                Used {s.usage_count}x
              </span>
              <span className="flex items-center gap-1">
                <BarChart3 className="w-3 h-3" />
                {Math.round(s.success_rate * 100)}%
              </span>
              <span className="text-dark-600">v{s.version}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
