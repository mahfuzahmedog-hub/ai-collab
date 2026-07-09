"use client";

import { useRef, useEffect, useState } from "react";
import { useStore } from "@/store";
import { sendChat } from "@/lib/websocket";
import { EventCard } from "@/components/timeline/EventCard";
import { Send, Bot, Sparkles } from "lucide-react";

export function Timeline() {
  const messages = useStore((s) => s.messages);
  const agents = useStore((s) => s.agents);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;
    sendChat(input.trim());
    setInput("");
  };

  const hasBoss = agents.some((a) => a.role === "boss");

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto scrollbar-thin py-2">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-sm">
              <div className="w-12 h-12 rounded-full bg-accent-500/10 border border-accent-500/20 flex items-center justify-center mx-auto mb-4">
                <Bot size={24} className="text-accent-400" />
              </div>
              <p className="text-base font-semibold text-white mb-1">Mission Control Ready</p>
              <p className="text-sm text-dark-400 mb-4 leading-relaxed">
                Your AI engineering team is standing by. Describe what you want to build and the Boss Agent will assemble a team.
              </p>
              <div className="flex items-center justify-center gap-1.5 text-xs text-dark-500">
                <Sparkles size={12} />
                <span>Type a message to get started</span>
                <Sparkles size={12} />
              </div>
            </div>
          </div>
        ) : (
          <div>
            {messages.map((msg, i) => (
              <EventCard key={msg.id} msg={msg} isLast={i === messages.length - 1} />
            ))}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-dark-700/60 p-3 bg-dark-950/50">
        <div className="flex gap-2 max-w-3xl">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder={hasBoss ? "Message the team..." : "Describe your project..."}
            className="flex-1 bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white placeholder-dark-500 focus:outline-none focus:border-accent-500/50 focus:ring-1 focus:ring-accent-500/20 transition-all"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            className="bg-accent-600 hover:bg-accent-700 disabled:bg-dark-700 disabled:text-dark-500 text-white px-3 py-2 rounded-lg transition-colors"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
