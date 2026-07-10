"use client";

import { formatDistanceToNow } from "date-fns";
import { Bot, FileText, Terminal, AlertCircle, CheckCircle } from "lucide-react";
import { sendCreateThread } from "@/lib/websocket";

interface EventCardProps {
  msg: {
    id: string;
    project_id: string;
    sender_id: string;
    sender_name: string;
    sender_role: string;
    content: string;
    msg_type: string;
    channel: string;
    thread_id?: string | null;
    reply_to: string | null;
    mentions: string[];
    attachments: any[];
    metadata: Record<string, any>;
    timestamp: string;
  };
  isLast: boolean;
  agents: { id: string; name: string; role: string; status: string }[];
  isStreaming?: boolean;
}

const ROLE_COLORS: Record<string, string> = {
  boss: "bg-primary-600",
  backend_engineer: "bg-blue-600",
  frontend_engineer: "bg-pink-600",
  researcher: "bg-purple-600",
  architect: "bg-amber-600",
  reviewer: "bg-green-600",
  qa_engineer: "bg-emerald-600",
  devops: "bg-orange-600",
  default: "bg-dark-600",
};

const ROLE_ICONS: Record<string, React.ReactNode> = {
  boss: <Bot className="w-4 h-4" />,
  backend_engineer: <Terminal className="w-4 h-4" />,
  frontend_engineer: <FileText className="w-4 h-4" />,
  reviewer: <CheckCircle className="w-4 h-4" />,
  qa_engineer: <AlertCircle className="w-4 h-4" />,
  default: <Bot className="w-4 h-4" />,
};

export function EventCard({ msg, isLast, agents, isStreaming }: EventCardProps) {
  const agent = agents.find((a) => a.id === msg.sender_id);
  const isUser = msg.sender_role === "user";
  const isSystem = msg.msg_type === "system";
  const isFile = msg.msg_type === "file";

  const roleColor = agent ? ROLE_COLORS[agent.role] || ROLE_COLORS.default : ROLE_COLORS.default;
  const roleIcon = agent ? ROLE_ICONS[agent.role] || ROLE_ICONS.default : ROLE_ICONS.default;

  let timeStr = "";
  try {
    timeStr = formatDistanceToNow(new Date(msg.timestamp), { addSuffix: true });
  } catch {
    timeStr = "just now";
  }

  if (isSystem) {
    return (
      <div className="flex items-start gap-3 opacity-70" style={{ borderLeft: isLast ? "2px solid transparent" : "2px solid #374151" }}>
        <div className="w-8 h-8 rounded-full bg-dark-700 flex items-center justify-center flex-shrink-0">
          <AlertCircle className="w-4 h-4 text-dark-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-xs text-dark-400 mb-1">{msg.content}</div>
          <div className="text-xs text-dark-500">{timeStr}</div>
        </div>
      </div>
    );
  }

  if (isFile) {
    return (
      <div className="flex items-start gap-3" style={{ borderLeft: isLast ? "2px solid transparent" : "2px solid #374151" }}>
        <div className="w-8 h-8 rounded-full bg-dark-700 flex items-center justify-center flex-shrink-0">
          <FileText className="w-4 h-4 text-blue-400" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 text-xs text-dark-400 mb-1">
            <span className="px-1.5 py-0.5 bg-blue-600/20 text-blue-400 rounded">FILE</span>
            <span>{timeStr}</span>
          </div>
          <div className="text-sm text-dark-200 font-mono bg-dark-800 p-2 rounded text-white">{msg.content}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3" style={{ borderLeft: isLast ? "2px solid transparent" : "2px solid #374151" }}>
      <div className="relative flex-shrink-0">
        <div className={`w-8 h-8 rounded-full ${roleColor} flex items-center justify-center text-white text-xs font-bold flex-shrink-0`}>
          {roleIcon}
        </div>
        {isStreaming && (
          <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-primary-500 rounded-full animate-pulse border-2 border-dark-950" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-medium text-white text-sm">{msg.sender_name}</span>
          <span className="text-xs text-dark-400 bg-dark-800 px-1.5 py-0.5 rounded">{msg.sender_role}</span>
          <span className="text-xs text-dark-500">{timeStr}</span>
          {msg.channel !== "general" && (
            <span className="text-xs text-primary-400 bg-primary-600/20 px-1.5 py-0.5 rounded">#{msg.channel}</span>
          )}
        </div>
        <div className="text-sm text-dark-100 whitespace-pre-wrap">{msg.content}</div>
        {!msg.thread_id && (
          <button
            onClick={() => sendCreateThread(msg.id, `Thread on ${msg.sender_name}'s message`, msg.channel)}
            className="mt-1 text-xs text-dark-400 hover:text-primary-400 transition-colors"
          >
            Reply in thread
          </button>
        )}
      </div>
    </div>
  );
}