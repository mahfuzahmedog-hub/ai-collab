"use client";

import { useStore } from "@/store";
import { clsx } from "clsx";

export function StatusBar() {
  const connected = useStore((s) => s.connected);
  const logs = useStore((s) => s.executionLogs);
  const totalTokens = logs.reduce((s, l) => s + (l.total_tokens || 0), 0);
  const totalCost = logs.reduce((s, l) => s + (l.cost_usd || 0), 0);

  return (
    <footer className="h-7 flex-shrink-0 border-t border-dark-700 bg-dark-900 flex items-center px-3 gap-4 text-[11px] text-dark-400">
      <span className="flex items-center gap-1.5">
        <span
          className={clsx(
            "w-1.5 h-1.5 rounded-full",
            connected ? "bg-green-500" : "bg-red-500"
          )}
        />
        {connected ? "Connected" : "Disconnected"}
      </span>
      <span>Tokens: {totalTokens.toLocaleString()}</span>
      <span>Cost: ${totalCost.toFixed(4)}</span>
      <div className="flex-1" />
      <span>AI Collab Workspace</span>
    </footer>
  );
}
