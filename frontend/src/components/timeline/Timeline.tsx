"use client";

import { useEffect, useRef, useState } from "react";
import { useStore } from "@/store";
import { sendChat, sendCommand } from "@/lib/websocket";
import { EventCard } from "./EventCard";
import { Send, Loader2 } from "lucide-react";

export function Timeline() {
  const messages = useStore((s) => s.messages);
  const agents = useStore((s) => s.agents);
  const activeChannel = useStore((s) => s.activeChannel);
  const streamingChunk = useStore((s) => s.streamingChunk);
  const [input, setInput] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  // Filter messages by active channel
  const channelMessages = messages.filter((m) => m.channel === activeChannel);

  // Auto-scroll
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [channelMessages, streamingChunk]);

  const handleSend = () => {
    if (!input.trim()) return;
    sendChat(input, activeChannel);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const hasBoss = agents.some((a) => a.role === "boss");

  return (
    <div className="flex flex-col h-full overflow-hidden bg-dark-950">
      {/* Channel header */}
      <div className="px-4 py-3 border-b border-dark-700 bg-dark-900">
        <div className="flex items-center gap-3">
          <span className="text-primary-400 font-mono text-sm">#{activeChannel}</span>
          <span className="text-dark-500 text-sm">|</span>
          <span className="text-dark-400 text-sm">
            {channelMessages.length} message{channelMessages.length !== 1 ? "s" : ""}
          </span>
        </div>
      </div>

      {/* Message list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {channelMessages.length === 0 && !streamingChunk && (
          <div className="flex flex-col items-center justify-center h-full text-dark-500">
            <div className="text-lg mb-2">No messages yet</div>
            <div className="text-sm">Start by sending a message or creating a project</div>
          </div>
        )}
        {channelMessages.map((msg, idx) => (
          <EventCard
            key={msg.id}
            msg={msg}
            isLast={idx === channelMessages.length - 1}
            agents={agents}
          />
        ))}
        {streamingChunk && !streamingChunk.done && (
          <EventCard
            msg={{
              id: `streaming-${streamingChunk.agentId}`,
              project_id: "",
              sender_id: streamingChunk.agentId,
              sender_name: agents.find((a) => a.id === streamingChunk.agentId)?.name || "Agent",
              sender_role: agents.find((a) => a.id === streamingChunk.agentId)?.role || "agent",
              content: streamingChunk.content + "▌",
              msg_type: "chat",
              channel: activeChannel,
              reply_to: null,
              mentions: [],
              attachments: [],
              metadata: {},
              timestamp: new Date().toISOString(),
            }}
            isLast={true}
            agents={agents}
            isStreaming={true}
          />
        )}
        <div ref={endRef} />
      </div>

      {/* Input bar */}
      <div className="p-4 border-t border-dark-700 bg-dark-900">
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={hasBoss ? `Message #${activeChannel}...` : "Create a project first"}
            disabled={!hasBoss}
            className="flex-1 bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-white placeholder-dark-500 resize-none focus:outline-none focus:ring-2 focus:ring-primary-500"
            rows={1}
            style={{ minHeight: "44px", maxHeight: "120px" }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || !hasBoss}
            className="p-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500 disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}