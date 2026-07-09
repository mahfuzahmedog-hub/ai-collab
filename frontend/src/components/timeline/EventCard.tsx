"use client";

import type { Message } from "@/types";
import { useState } from "react";
import {
  User,
  Bot,
  Crown,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Terminal,
  Code2,
  FileText,
  MessageSquare,
  ChevronDown,
  ChevronRight,
  Clock,
} from "lucide-react";
import { clsx } from "clsx";

const roleConfig: Record<string, { color: string; icon: any }> = {
  boss: { color: "text-accent-400 border-accent-500/30 bg-accent-500/10", icon: Crown },
  user: { color: "text-blue-400 border-blue-500/30 bg-blue-500/10", icon: User },
  backend_engineer: { color: "text-cyan-400 border-cyan-500/30 bg-cyan-500/10", icon: Terminal },
  frontend_engineer: { color: "text-pink-400 border-pink-500/30 bg-pink-500/10", icon: Code2 },
  planner: { color: "text-purple-400 border-purple-500/30 bg-purple-500/10", icon: FileText },
  researcher: { color: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10", icon: Bot },
  reviewer: { color: "text-orange-400 border-orange-500/30 bg-orange-500/10", icon: CheckCircle2 },
  default: { color: "text-dark-400 border-dark-600/30 bg-dark-700/30", icon: MessageSquare },
};

const msgTypeIcon: Record<string, any> = {
  system: Terminal,
  task_update: Loader2,
  review: CheckCircle2,
};

export function EventCard({ msg, isLast }: { msg: Message; isLast: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const isUser = msg.sender_role === "user";
  const isSystem = msg.msg_type === "system";
  const config = roleConfig[msg.sender_role] || roleConfig.default;
  const Icon = msgTypeIcon[msg.msg_type] || config.icon;

  const isProgress = msg.content.includes("Progress Update");

  return (
    <div className={clsx(
      "relative flex gap-3 px-4 py-2.5 group transition-colors animate-fade-in",
      isSystem ? "opacity-70" : "hover:bg-dark-800/30"
    )}>
      {!isLast && (
        <div className="timeline-line absolute left-[23px] top-9 bottom-0 w-[1.5px]" />
      )}

      <div className={clsx(
        "w-8 h-8 rounded-full flex items-center justify-center shrink-0 border",
        config.color,
        isUser ? "bg-blue-600/20 border-blue-500/40" : ""
      )}>
        <Icon size={14} />
      </div>

      <div className="flex-1 min-w-0 space-y-0.5">
        <div className="flex items-center gap-2">
          <span className={clsx(
            "text-xs font-semibold",
            isUser ? "text-blue-300" : isSystem ? "text-dark-400" : config.color.split(" ")[0]
          )}>
            {isUser ? "You" : msg.sender_name}
          </span>
          <span className="text-[10px] text-dark-600 capitalize">
            {msg.sender_role.replace(/_/g, " ")}
          </span>
          <span className="text-[10px] text-dark-600 ml-auto flex items-center gap-1">
            <Clock size={10} />
            {new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>
        </div>

        {isProgress ? (
          <div>
            <button
              onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-1 text-xs text-accent-400 hover:text-accent-300 transition-colors"
            >
              {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
              Progress Update
            </button>
            {expanded && (
              <pre className="mt-1 text-xs text-dark-300 whitespace-pre-wrap font-sans">
                {msg.content.replace("📊 Progress Update:\n", "")}
              </pre>
            )}
          </div>
        ) : (
          <p className={clsx(
            "text-sm whitespace-pre-wrap break-words",
            isSystem ? "text-dark-500 italic" : "text-dark-100"
          )}>
            {msg.content}
          </p>
        )}
      </div>
    </div>
  );
}
