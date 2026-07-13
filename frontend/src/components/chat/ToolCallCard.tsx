"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, Loader2, CheckCircle, XCircle } from "lucide-react";

interface ToolCallCardProps {
  toolName: string;
  arguments: string;
  result?: string;
  status: "pending" | "running" | "completed" | "failed";
}

export function ToolCallCard({ toolName, arguments: args, result, status }: ToolCallCardProps) {
  const [expanded, setExpanded] = useState(false);

  let icon;
  let border;
  if (status === "running") {
    icon = <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin" />;
    border = "border-blue-500/30";
  } else if (status === "completed") {
    icon = <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />;
    border = "border-emerald-500/30";
  } else if (status === "failed") {
    icon = <XCircle className="w-3.5 h-3.5 text-red-400" />;
    border = "border-red-500/30";
  } else {
    icon = <Loader2 className="w-3.5 h-3.5 text-dark-400" />;
    border = "border-dark-600";
  }

  let prettyArgs = "";
  try {
    prettyArgs = JSON.stringify(JSON.parse(args || "{}"), null, 2);
  } catch {
    prettyArgs = args || "{}";
  }

  return (
    <div className={`border ${border} rounded-lg bg-dark-800/50 overflow-hidden`}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-3 py-2 text-xs text-left hover:bg-dark-700/50 transition-colors"
      >
        {expanded ? <ChevronDown className="w-3 h-3 text-dark-400" /> : <ChevronRight className="w-3 h-3 text-dark-400" />}
        {icon}
        <span className="font-mono text-dark-200">{toolName}</span>
        {status === "running" && <span className="text-blue-400 ml-auto">Running...</span>}
        {status === "completed" && <span className="text-emerald-400 ml-auto">Done</span>}
        {status === "failed" && <span className="text-red-400 ml-auto">Failed</span>}
      </button>
      {expanded && (
        <div className="px-3 pb-2 space-y-2">
          <div>
            <span className="text-[10px] text-dark-500 uppercase tracking-wide">Arguments</span>
            <pre className="text-[11px] text-dark-300 font-mono bg-dark-900 p-2 rounded mt-1 overflow-x-auto">{prettyArgs}</pre>
          </div>
          {result !== undefined && (
            <div>
              <span className="text-[10px] text-dark-500 uppercase tracking-wide">Result</span>
              <pre className="text-[11px] text-dark-300 font-mono bg-dark-900 p-2 rounded mt-1 overflow-x-auto max-h-32 overflow-y-auto">{result}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
