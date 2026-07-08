import type { Message } from "@/types";

const roleColors: Record<string, string> = {
  boss: "text-yellow-400",
  user: "text-blue-400",
  planner: "text-purple-400",
  researcher: "text-green-400",
  architect: "text-orange-400",
  backend_engineer: "text-cyan-400",
  frontend_engineer: "text-pink-400",
  reviewer: "text-red-400",
  qa_engineer: "text-emerald-400",
  devops: "text-slate-400",
  security_engineer: "text-rose-400",
  database_engineer: "text-indigo-400",
  documentation_writer: "text-teal-400",
};

const typeColors: Record<string, string> = {
  system: "text-dark-400 italic",
  task_update: "text-accent-400",
  review: "text-yellow-400",
};

export function ChatMessage({ msg }: { msg: Message }) {
  const isUser = msg.sender_role === "user";
  const roleColor = roleColors[msg.sender_role] || "text-white";
  const typeClass = typeColors[msg.msg_type] || "";

  return (
    <div className={`group py-2 px-4 hover:bg-dark-800/50 transition-colors ${typeClass}`}>
      <div className="flex items-start gap-3">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
          isUser ? "bg-blue-600" : "bg-dark-600"
        }`}>
          {msg.sender_name.charAt(0).toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className={`text-sm font-semibold ${roleColor}`}>
              {msg.sender_name}
            </span>
            <span className="text-xs text-dark-500 capitalize">
              {msg.sender_role.replace(/_/g, " ")}
            </span>
            <span className="text-xs text-dark-600 ml-auto">
              {new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
          </div>
          <p className="text-sm text-dark-100 whitespace-pre-wrap break-words">
            {msg.content}
          </p>
        </div>
      </div>
    </div>
  );
}
