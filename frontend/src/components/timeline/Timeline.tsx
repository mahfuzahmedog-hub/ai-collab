"use client";

import { useEffect, useRef } from "react";
import { useStore } from "@/store";
import { EventCard } from "./EventCard";
import { ThreadView } from "./ThreadView";
import { MessageComposer } from "@/features/chat/MessageComposer";

export function Timeline() {
  const messages = useStore((s) => s.messages);
  const agents = useStore((s) => s.agents);
  const activeChannel = useStore((s) => s.activeChannel);
  const streamingChunk = useStore((s) => s.streamingChunk);
  const activeThread = useStore((s) => s.activeThread);
  const threads = useStore((s) => s.threads);
  const endRef = useRef<HTMLDivElement>(null);

  // Filter messages by active channel, excluding thread replies.
  // ponytail: cap the rendered window to the last 300 for perf instead of a
  // full virtualization dep; upgrade path is react-window if channels get huge.
  const channelMessages = messages
    .filter((m) => m.channel === activeChannel && !m.thread_id)
    .slice(-300);

  // Get thread messages for active thread
  const threadMessages = activeThread
    ? messages.filter((m) => m.thread_id === activeThread)
    : [];

  // Auto-scroll
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [channelMessages, streamingChunk, threadMessages]);

  const hasBoss = agents.some((a) => a.role === "boss" || a.role === "coworker");

  return (
    <div className="flex flex-col h-full overflow-hidden bg-dark-950">
      {/* Channel header */}
      <div className="px-4 py-3 border-b border-dark-700 bg-dark-900">
        <div className="flex items-center gap-3">
          <span className="text-primary-400 font-mono text-sm">{activeChannel.startsWith("#") ? activeChannel : `#${activeChannel}`}</span>
          <span className="text-dark-500 text-sm">|</span>
          <span className="text-dark-400 text-sm">
            {channelMessages.length} message{channelMessages.length !== 1 ? "s" : ""}
          </span>
        </div>
      </div>

      {/* Body: message list + thread panel side-by-side */}
      <div className="flex flex-1 overflow-hidden">
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
                thread_id: null,
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

        {/* Thread panel */}
        <ThreadView />
      </div>

      {/* Input bar */}
      <div className="p-4 border-t border-dark-700 bg-dark-900">
        <MessageComposer
          channel={activeChannel}
          disabled={!hasBoss}
          placeholder={hasBoss ? `Message #${activeChannel}...` : "Create a project first"}
        />
      </div>
    </div>
  );
}