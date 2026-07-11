"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useStore } from "@/store";
import { sendPauseAgent, sendResumeAgent } from "@/lib/websocket";
import { clsx } from "clsx";
import { X, MessageSquare, Pause, Play, Activity } from "lucide-react";
import type { AgentStatus } from "@/types";

const STATUS_EMOJI: Record<string, string> = {
  idle: "😴",
  thinking: "🧠",
  working: "💻",
  researching: "🔍",
  collaborating: "🤝",
  reviewing: "📝",
  waiting_for_dependencies: "⏸️",
  blocked: "🚫",
  error: "❌",
  retired: "👋",
};

function statusLabel(status: AgentStatus): string {
  return status.replace(/_/g, " ");
}

export function AgentProfile() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const activeAgentProfile = useStore((s) => s.activeAgentProfile);
  const agents = useStore((s) => s.agents);
  const executionLogs = useStore((s) => s.executionLogs);
  const setActiveAgentProfile = useStore((s) => s.setActiveAgentProfile);
  const setActiveChannel = useStore((s) => s.setActiveChannel);

  const agent = agents.find((a) => a.id === activeAgentProfile) || null;

  const recentLogs =
    agent == null
      ? []
      : executionLogs
          .filter((l) => l.agent_id === agent.id || l.agent_name === agent.name)
          .slice(0, 10);

  const close = () => setActiveAgentProfile(null);

  const goToChat = () => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("tab", "chat");
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  };

  const openPrivateChat = () => {
    if (!agent) return;
    const dmId = `dm-${agent.name.toLowerCase().replace(/\s+/g, "-")}`;
    setActiveChannel(dmId);
    setActiveAgentProfile(null);
    goToChat();
  };

  return (
    <AnimatePresence>
      {agent && (
        <motion.div
          className="fixed inset-0 z-50 flex justify-end"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div className="absolute inset-0 bg-black/50" onClick={close} />

          <motion.aside
            className="relative w-full max-w-sm h-full bg-dark-900 border-l border-dark-700 shadow-2xl flex flex-col"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "tween", duration: 0.25 }}
          >
            <div className="flex items-start justify-between p-4 border-b border-dark-700">
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-12 h-12 rounded-full bg-primary-600 flex items-center justify-center text-white text-xl font-bold flex-shrink-0">
                  {agent.emoji || agent.name.charAt(0)}
                </div>
                <div className="min-w-0">
                  <div className="text-white font-semibold truncate">
                    {agent.display_name || agent.name}
                  </div>
                  <div className="text-xs text-dark-400 truncate">{agent.role.replace(/_/g, " ")}</div>
                </div>
              </div>
              <button
                onClick={close}
                className="text-dark-400 hover:text-white transition-colors"
                title="Close"
              >
                <X size={18} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              <div
                className={clsx(
                  "flex items-center gap-2 text-sm rounded-md px-2 py-1.5 border",
                  agent.status === "blocked" || agent.status === "error"
                    ? "bg-red-500/10 border-red-500/30 text-red-300"
                    : "bg-dark-800 border-dark-700 text-dark-300"
                )}
              >
                <span className="text-lg">{STATUS_EMOJI[agent.status] || "🤖"}</span>
                <span className="capitalize">{statusLabel(agent.status)}</span>
                {agent.version && (
                  <span className="ml-auto text-xs text-dark-500">v{agent.version}</span>
                )}
              </div>

              {agent.mission && (
                <div>
                  <div className="text-xs uppercase tracking-wide text-dark-500 mb-1">Mission</div>
                  <p className="text-sm text-dark-300">{agent.mission}</p>
                </div>
              )}

              {agent.skills.length > 0 && (
                <div>
                  <div className="text-xs uppercase tracking-wide text-dark-500 mb-1">Skills</div>
                  <div className="flex flex-wrap gap-1.5">
                    {agent.skills.map((skill) => (
                      <span
                        key={skill}
                        className="text-xs bg-primary-600/15 text-primary-400 border border-primary-600/20 rounded-full px-2 py-0.5"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="bg-dark-800 rounded-md p-2">
                  <div className="text-xs text-dark-500">Current Task</div>
                  <div className="text-dark-300 truncate">
                    {agent.current_task_id || "—"}
                  </div>
                </div>
                <div className="bg-dark-800 rounded-md p-2">
                  <div className="text-xs text-dark-500">Provider</div>
                  <div className="text-dark-300 truncate">{agent.provider}</div>
                </div>
                <div className="bg-dark-800 rounded-md p-2 col-span-2">
                  <div className="text-xs text-dark-500">Model</div>
                  <div className="text-dark-300 truncate">{agent.model}</div>
                </div>
              </div>

              <div>
                <div className="text-xs uppercase tracking-wide text-dark-500 mb-2 flex items-center gap-1">
                  <Activity size={12} /> Recent Activity
                </div>
                {recentLogs.length === 0 ? (
                  <div className="text-xs text-dark-500">No activity yet.</div>
                ) : (
                  <div className="space-y-1.5">
                    {recentLogs.map((log) => (
                      <div
                        key={log.id}
                        className="bg-dark-800 rounded-md p-2 text-xs flex flex-col gap-0.5"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-dark-300 font-mono truncate">{log.model}</span>
                          <span className="text-dark-500">{log.total_tokens} tok</span>
                        </div>
                        <div className="flex items-center justify-between text-dark-500">
                          <span className="truncate">{log.action}</span>
                          <span>{log.latency_ms}ms</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="p-4 border-t border-dark-700 flex flex-col gap-2">
              <button
                onClick={openPrivateChat}
                className="w-full flex items-center justify-center gap-2 bg-primary-600 hover:bg-primary-500 text-white rounded-md py-2 text-sm font-medium transition-colors"
              >
                <MessageSquare size={15} /> Private Chat
              </button>
              {agent.status === "paused" ? (
                <button
                  onClick={() => sendResumeAgent(agent.id)}
                  className="w-full flex items-center justify-center gap-2 bg-dark-800 hover:bg-dark-700 border border-dark-700 text-white rounded-md py-2 text-sm transition-colors"
                >
                  <Play size={15} /> Resume
                </button>
              ) : (
                <button
                  onClick={() => sendPauseAgent(agent.id)}
                  className="w-full flex items-center justify-center gap-2 bg-dark-800 hover:bg-dark-700 border border-dark-700 text-white rounded-md py-2 text-sm transition-colors"
                >
                  <Pause size={15} /> Pause
                </button>
              )}
            </div>
          </motion.aside>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
