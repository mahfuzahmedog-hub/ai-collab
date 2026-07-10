"use client";

import { useStore } from "@/store";
import { sendChat } from "@/lib/websocket";
import { useState, useRef, useEffect } from "react";
import { EventCard } from "./EventCard";
import { X } from "lucide-react";

export function ThreadView() {
  const activeThread = useStore((s) => s.activeThread);
  const setActiveThread = useStore((s) => s.setActiveThread);
  const messages = useStore((s) => s.messages);
  const agents = useStore((s) => s.agents);
  const threads = useStore((s) => s.threads);
  const [input, setInput] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  const thread = threads.find((t) => t.id === activeThread);
  const threadMessages = messages.filter((m) => m.thread_id === activeThread);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [threadMessages]);

  if (!activeThread || !thread) return null;

  const handleSend = () => {
    if (!input.trim() || !thread) return;
    sendChat(input, thread.channel);
    setInput("");
  };

  return (
    <div className="w-96 flex-shrink-0 border-l border-dark-700 bg-dark-900 flex flex-col h-full overflow-hidden">
      <div className="px-4 py-3 border-b border-dark-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-white">{thread.title}</span>
          <span className="text-xs text-dark-400">Thread</span>
        </div>
        <button onClick={() => setActiveThread(null)} className="text-dark-400 hover:text-white p-1 rounded">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {threadMessages.map((msg, idx) => (
          <EventCard
            key={msg.id}
            msg={msg}
            isLast={idx === threadMessages.length - 1}
            agents={agents}
          />
        ))}
        <div ref={endRef} />
      </div>

      <div className="px-4 py-3 border-t border-dark-700">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), handleSend())}
          placeholder={`Reply in thread...`}
          className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-white placeholder-dark-500 resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
          rows={2}
        />
      </div>
    </div>
  );
}
