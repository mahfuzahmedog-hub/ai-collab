"use client";

import { useStore } from "@/store";
import { Search, Bell, Settings, HelpCircle } from "lucide-react";
import { clsx } from "clsx";

export function TopBar() {
  const project = useStore((s) => s.project);
  const connected = useStore((s) => s.connected);

  return (
    <header className="h-12 border-b border-dark-700/60 flex items-center px-4 gap-3 bg-dark-950/80 backdrop-blur-md z-20 shrink-0">
      <h1 className="text-sm font-semibold text-white truncate min-w-0">
        {project?.title || "AI Collaboration Platform"}
      </h1>

      <div className="flex items-center gap-1.5 ml-2">
        <div className={clsx("w-1.5 h-1.5 rounded-full", connected ? "bg-green-500 pulse-working" : "bg-red-500")} />
        <span className="text-[10px] text-dark-400 font-medium">{connected ? "Live" : "Offline"}</span>
      </div>

      <div className="flex-1" />

      <div className="hidden sm:flex items-center gap-1.5 bg-dark-800 border border-dark-700 rounded-md px-2.5 py-1.5 text-dark-400 w-48">
        <Search size={14} />
        <span className="text-xs">Search events...</span>
        <span className="ml-auto text-[10px] text-dark-600 bg-dark-700 px-1 rounded">Ctrl+K</span>
      </div>

      <button className="text-dark-400 hover:text-dark-200 transition-colors" title="Help">
        <HelpCircle size={16} />
      </button>

      <button className="text-dark-400 hover:text-dark-200 transition-colors relative" title="Notifications">
        <Bell size={16} />
        <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 bg-accent-500 rounded-full" />
      </button>

      <button className="text-dark-400 hover:text-dark-200 transition-colors" title="Settings">
        <Settings size={16} />
      </button>
    </header>
  );
}
