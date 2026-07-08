"use client";

import { useRef, useEffect, useState } from "react";
import { useStore } from "@/store";
import { sendChat } from "@/lib/websocket";
import { ChatMessage } from "@/components/chat/ChatMessage";

export function Workspace() {
  const messages = useStore((s) => s.messages);
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

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto scrollbar-thin py-2">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-dark-500">
            <div className="text-center max-w-md">
              <div className="text-4xl mb-4">👑</div>
              <p className="text-lg font-semibold text-white mb-2">Your Boss Agent is Ready</p>
              <p className="text-sm text-dark-400 mb-3">
                The Boss Agent is your engineering manager. Describe your project and it will assemble a team of specialized AI agents to build it.
              </p>
              <div className="text-xs text-dark-500 space-y-1">
                <p>💬 Tell the Boss what you want to build</p>
                <p>🤖 Agents are created and assigned tasks automatically</p>
                <p>📋 Track progress on the Task Board</p>
              </div>
              <p className="text-sm text-accent-400 mt-4">Type a message to start your project!</p>
            </div>
          </div>
        )}
        {messages.map((msg) => (
          <ChatMessage key={msg.id} msg={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-dark-700 p-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Type a message to the team..."
            className="flex-1 bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white placeholder-dark-400 focus:outline-none focus:border-accent-500"
          />
          <button
            onClick={handleSend}
            className="bg-accent-600 hover:bg-accent-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
