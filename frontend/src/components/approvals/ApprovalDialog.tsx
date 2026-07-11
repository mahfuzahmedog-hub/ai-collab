"use client";
import { useStore } from "@/store";
import { sendCommand } from "@/lib/websocket";
import { useState } from "react";

export function ApprovalDialog() {
  const approvals = useStore((s) => s.approvals);
  const [hidden, setHidden] = useState(true);
  const pending = approvals.filter((a) => a.status === "pending");
  if (pending.length === 0) return null;
  return (
    <div className="fixed bottom-4 right-4 z-50 max-w-sm w-full">
      {hidden ? (
        <button onClick={() => setHidden(false)} className="bg-yellow-600 hover:bg-yellow-500 text-white rounded-full px-4 py-2 text-sm font-semibold shadow-lg flex items-center gap-2">
          <span>⏳</span> {pending.length} pending approval{pending.length > 1 ? "s" : ""}
        </button>
      ) : (
        <div className="bg-dark-800 border border-dark-600 rounded-lg shadow-2xl overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-dark-600">
            <h3 className="text-sm font-bold text-white">Pending Approvals</h3>
            <button onClick={() => setHidden(true)} className="text-dark-400 hover:text-white text-lg leading-none">&times;</button>
          </div>
          <div className="max-h-80 overflow-y-auto divide-y divide-dark-600">
            {pending.map((a) => (
              <div key={a.id} className="px-4 py-3 space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-white truncate">{a.action}</p>
                    <p className="text-xs text-dark-400 mt-0.5">{a.agent_name}</p>
                  </div>
                </div>
                {a.description && <p className="text-xs text-dark-300 leading-relaxed">{a.description}</p>}
                <div className="flex gap-2 pt-1">
                  <button onClick={() => { sendCommand("approve", { approval_id: a.id }); }} className="flex-1 bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-semibold py-1.5 rounded transition-colors">Approve</button>
                  <button onClick={() => { sendCommand("reject", { approval_id: a.id }); }} className="flex-1 bg-red-800 hover:bg-red-700 text-white text-xs font-semibold py-1.5 rounded transition-colors">Reject</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
