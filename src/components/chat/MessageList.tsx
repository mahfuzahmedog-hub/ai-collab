import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Clock, Bot, User, Code, FileText } from "lucide-react";
import { format } from "date-fns";

interface Message {
  _id: string;
  channelId: string;
  senderName: string;
  senderType: "user" | "agent";
  agentId?: string;
  content: string;
  contentType: string;
  createdAt: number;
  mentions?: string[];
}

interface Agent {
  _id: string;
  name: string;
  emoji?: string;
  color?: string;
}

interface MessageListProps {
  messages: Message[];
  agents: Agent[];
  currentUserId?: string;
  loading?: boolean;
}

export function MessageList({ messages, agents, currentUserId, loading }: MessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const getAgentForMessage = (agentId?: string) => {
    if (!agentId) return null;
    return agents.find((a) => a._id === agentId);
  };

  const formatTime = (timestamp: number) => {
    return format(new Date(timestamp), "h:mm a");
  };

  const formatDate = (timestamp: number) => {
    const now = new Date();
    const date = new Date(timestamp);
    const isToday = now.toDateString() === date.toDateString();
    const isYesterday = new Date(now.getTime() - 86400000).toDateString() === date.toDateString();
    
    if (isToday) return "Today";
    if (isYesterday) return "Yesterday";
    return format(date, "MMM d, yyyy");
  };

  // Group messages by date
  const groupedMessages: { date: string; messages: Message[] }[] = [];
  let currentDate = "";

  for (const msg of messages) {
    const msgDate = formatDate(msg.createdAt);
    if (msgDate !== currentDate) {
      currentDate = msgDate;
      groupedMessages.push({ date: msgDate, messages: [msg] });
    } else {
      groupedMessages[groupedMessages.length - 1].messages.push(msg);
    }
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <Clock className="h-8 w-8 animate-spin" />
          <p className="text-sm">Loading messages...</p>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea ref={scrollRef} className="flex-1 px-4">
      <div className="py-4 space-y-0">
        {/* Welcome message */}
        <div className="flex items-center gap-3 py-6">
          <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center">
            <Bot className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h2 className="font-semibold text-lg">AIOS Team Chat</h2>
            <p className="text-sm text-muted-foreground">
              Chat with your AI agent team. All agents see messages here.
            </p>
          </div>
        </div>

        {groupedMessages.map((group, gi) => (
          <div key={gi}>
            {/* Date separator */}
            <div className="flex items-center gap-3 py-3">
              <div className="flex-1 h-px bg-border" />
              <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
                {group.date}
              </span>
              <div className="flex-1 h-px bg-border" />
            </div>

            {group.messages.map((msg, mi) => {
              const agent = getAgentForMessage(msg.agentId);
              const isAgent = msg.senderType === "agent";
              const isSystem = msg.contentType === "system";
              const prevMsg = mi > 0 ? group.messages[mi - 1] : null;
              const sameSender = prevMsg && prevMsg.senderName === msg.senderName && prevMsg.senderType === msg.senderType;

              return (
                <motion.div
                  key={msg._id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2, delay: mi * 0.02 }}
                  className={cn(
                    "group flex gap-3 px-4 py-1.5 rounded-lg -mx-4 transition-colors",
                    isSystem ? "hover:bg-muted/30" : "hover:bg-muted/20",
                  )}
                >
                  {/* Avatar */}
                  <div className={cn(
                    "shrink-0 flex items-start",
                    sameSender ? "invisible" : "pt-0.5"
                  )}>
                    <div className={cn(
                      "h-9 w-9 rounded-lg flex items-center justify-center text-lg font-medium",
                      isAgent
                        ? (agent?.color ? "" : "bg-gradient-to-br from-purple-500 to-blue-500")
                        : "bg-gradient-to-br from-green-500 to-emerald-500",
                    )}
                    style={agent?.color ? { backgroundColor: agent.color } : undefined}
                    >
                      <span>{isAgent ? (agent?.emoji ?? "🤖") : "👤"}</span>
                    </div>
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    {!sameSender && (
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className={cn(
                          "font-semibold text-sm",
                          isAgent && agent?.color ? "" : "",
                        )}
                        style={isAgent && agent?.color ? { color: agent.color } : undefined}
                        >
                          {msg.senderName}
                        </span>
                        <Badge
                          variant={isAgent ? "default" : "secondary"}
                          className="h-4 text-[10px] px-1.5 font-normal"
                        >
                          {isAgent ? "Agent" : "You"}
                        </Badge>
                        <span className="text-[11px] text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">
                          {formatTime(msg.createdAt)}
                        </span>
                      </div>
                    )}

                    <div className="text-sm leading-relaxed text-foreground/90 whitespace-pre-wrap break-words">
                      {msg.contentType === "code" ? (
                        <div className="bg-muted rounded-lg p-3 font-mono text-xs overflow-x-auto my-1 border">
                          <div className="flex items-center gap-1.5 mb-2 text-muted-foreground text-[10px] uppercase tracking-wider">
                            <Code className="h-3 w-3" />
                            Code
                          </div>
                          <pre className="text-foreground/80">{msg.content}</pre>
                        </div>
                      ) : (
                        msg.content
                      )}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}
