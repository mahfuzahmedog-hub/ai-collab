import { useState, useEffect, useCallback } from "react";
import { useQuery, useMutation, useAction } from "convex/react";
import { useAuth } from "@/hooks/use-auth";
import { useAuthActions } from "@convex-dev/auth/react";
import { api } from "@/convex/_generated/api";
import { Id } from "@/convex/_generated/dataModel";
import { ChannelSidebar } from "@/components/chat/ChannelSidebar";
import { MessageList } from "@/components/chat/MessageList";
import { MessageInput } from "@/components/chat/MessageInput";
import { LogoDropdown } from "@/components/LogoDropdown";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Hash, Bot, Phone, Pin, Inbox, HelpCircle, Loader2 } from "lucide-react";
import { Toaster } from "sonner";

interface Agent {
  _id: Id<"agents">;
  name: string;
  emoji?: string;
  color?: string;
  status: string;
  type: string;
  description?: string;
  capabilities?: string[];
}

interface Channel {
  _id: Id<"channels">;
  name: string;
  type: "group" | "direct" | "thread";
  agentIds: Id<"agents">[];
  isDefault?: boolean;
}

interface Message {
  _id: Id<"messages">;
  channelId: Id<"channels">;
  senderName: string;
  senderType: "user" | "agent";
  agentId?: Id<"agents">;
  content: string;
  contentType: string;
  createdAt: number;
  mentions?: Id<"agents">[];
}

export default function ChatPage() {
  const { user, isLoading: authLoading, isAuthenticated } = useAuth();
  const { signIn } = useAuthActions();
  const [selectedChannelId, setSelectedChannelId] = useState<string | null>(null);
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null);

  // Queries
  const projects = useQuery(api.projects.list);
  const agents = useQuery(
    api.agents.list,
    currentProjectId ? { projectId: currentProjectId as Id<"projects"> } : "skip",
  );
  const channels = useQuery(
    api.channels.list,
    currentProjectId ? { projectId: currentProjectId as Id<"projects"> } : "skip",
  );
  const messages = useQuery(
    api.messages.list,
    selectedChannelId ? { channelId: selectedChannelId as Id<"channels">, limit: 50 } : "skip",
  );
  const unreadCount = useQuery(api.notifications.unreadCount);

  // Actions (call backend LLM orchestration)
  const processUserMessage = useAction(api.agentOrchestration.processUserMessage);
  const sendWelcomeMessage = useAction(api.agentOrchestration.sendWelcomeMessage);

  // Mutations (for setup only)
  const createProject = useMutation(api.projects.create);
  const setupDefaultAgents = useMutation(api.agents.setupDefaultAgents);
  const setupDefaultChannels = useMutation(api.channels.setupDefaultChannels);

  // Auto-login as anonymous guest
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      signIn("anonymous");
    }
  }, [authLoading, isAuthenticated, signIn]);

  // Initialize project + agents + channels
  useEffect(() => {
    if (projects && projects.length === 0 && !authLoading) {
      initializeProject();
    } else if (projects && projects.length > 0 && !currentProjectId) {
      const firstProject = projects[0];
      if (firstProject) {
        setCurrentProjectId(firstProject._id);
      }
    }
  }, [projects, authLoading]);

  const initializeProject = async () => {
    try {
      const projectId = await createProject({
        name: "My AIOS Project",
        description: "AI Agent Operating System",
        goal: "Build amazing things with AI agent collaboration",
      });
      const agentIds = await setupDefaultAgents({ projectId: projectId as Id<"projects"> });
      const channels = await setupDefaultChannels({
        projectId: projectId as Id<"projects">,
        agentIds: agentIds as Id<"agents">[],
      });
      setCurrentProjectId(projectId);
      setSelectedChannelId(channels.groupChannelId);
      // Send welcome message from the Boss agent
      sendWelcomeMessage({
        channelId: channels.groupChannelId as Id<"channels">,
        projectId: projectId as Id<"projects">,
      });
    } catch (error) {
      console.error("Failed to initialize project:", error);
    }
  };

  // Auto-select default channel
  useEffect(() => {
    if (channels && channels.length > 0 && !selectedChannelId) {
      const groupChannel = channels.find((c: Channel) => c.type === "group");
      setSelectedChannelId(groupChannel ? groupChannel._id : channels[0]._id);
    }
  }, [channels, selectedChannelId]);

  const handleSendMessage = useCallback(
    async (content: string, contentType?: string) => {
      if (!selectedChannelId || !currentProjectId || !user) return;
      try {
        await processUserMessage({
          channelId: selectedChannelId as Id<"channels">,
          projectId: currentProjectId as Id<"projects">,
          content,
          contentType: (contentType as "text" | "code") ?? "text",
        });
      } catch (error) {
        console.error("Failed to process message:", error);
      }
    },
    [selectedChannelId, currentProjectId, user, processUserMessage],
  );

  const handleSelectDirectMessage = (agentId: string) => {
    if (channels) {
      const directChannel = channels.find(
        (c: Channel) => c.type === "direct" && c.agentIds.includes(agentId as Id<"agents">),
      );
      if (directChannel) {
        setSelectedChannelId(directChannel._id);
      }
    }
  };

  const displayMessages = messages ? [...messages].reverse() : [];
  const selectedChannel = channels?.find((c: Channel) => c._id === selectedChannelId);
  const currentAgents = (agents ?? []) as unknown as Agent[];

  return (
    <div className="h-screen flex flex-col bg-background">
      <div className="flex flex-1 overflow-hidden">
        <div className="w-64 shrink-0 hidden md:block">
          <ChannelSidebar
            agents={currentAgents}
            channels={(channels ?? []) as unknown as Channel[]}
            selectedChannelId={selectedChannelId}
            onSelectChannel={setSelectedChannelId}
            onSelectDirectMessage={handleSelectDirectMessage}
            unreadCount={unreadCount ?? 0}
          />
        </div>

        <div className="flex-1 flex flex-col min-w-0">
          <div className="h-12 flex items-center justify-between px-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="flex items-center gap-2">
              <Hash className="h-5 w-5 text-muted-foreground" />
              <span className="font-semibold text-sm">
                {selectedChannel?.type === "group" ? "Team Chat"
                  : selectedChannel?.type === "direct"
                    ? currentAgents.find((a: Agent) => selectedChannel?.agentIds.includes(a._id))?.name ?? "Agent Chat"
                    : "Chat"}
              </span>
              <Badge variant="secondary" className="h-5 text-[10px] px-1.5 font-normal">
                {selectedChannel?.type === "group" ? `${currentAgents.length} agents` : "direct"}
              </Badge>
            </div>
            <div className="flex items-center gap-1">
              <Button variant="ghost" size="icon" className="h-8 w-8 rounded-lg"><Phone className="h-4 w-4 text-muted-foreground/60" /></Button>
              <Button variant="ghost" size="icon" className="h-8 w-8 rounded-lg"><Pin className="h-4 w-4 text-muted-foreground/60" /></Button>
              <Button variant="ghost" size="icon" className="h-8 w-8 rounded-lg"><HelpCircle className="h-4 w-4 text-muted-foreground/60" /></Button>
              <Separator orientation="vertical" className="h-6 mx-1" />
              <LogoDropdown />
            </div>
          </div>

          {selectedChannelId ? (
            <>
              <MessageList messages={(displayMessages ?? []) as unknown as Message[]} agents={currentAgents} currentUserId={user?._id} />
              <MessageInput onSend={handleSendMessage} agents={currentAgents} placeholder={`Message #${selectedChannel?.type === "group" ? "team-chat" : "direct"}`} />
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <Bot className="h-12 w-12 mx-auto text-muted-foreground/30 mb-4" />
                <h3 className="text-lg font-semibold text-muted-foreground">
                  {authLoading ? "Loading..." : "Select a channel"}
                </h3>
                <p className="text-sm text-muted-foreground/60 mt-1">Choose a channel to start chatting</p>
              </div>
            </div>
          )}
        </div>

        <div className="w-60 shrink-0 border-l bg-muted/10 hidden xl:block">
          <div className="h-12 flex items-center px-4 border-b"><span className="text-sm font-semibold">Team</span></div>
          <ScrollArea className="h-[calc(100%-48px)]">
            <div className="p-3 space-y-3">
              <div>
                <h4 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/60 mb-2 px-1">
                  Online — {currentAgents.filter(a => a.status !== "retired").length}
                </h4>
                <div className="space-y-1">
                  {currentAgents.filter((a: Agent) => a.status !== "retired").map((agent: Agent) => (
                    <div key={agent._id} className="flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-muted/50 transition-colors cursor-pointer" onClick={() => handleSelectDirectMessage(agent._id)}>
                      <span className="text-lg">{agent.emoji ?? "🤖"}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{agent.name}</p>
                        <p className="text-[10px] text-muted-foreground/60 capitalize">{agent.type} · {agent.status}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <Separator />
              <div className="px-2">
                <h4 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/60 mb-2">About</h4>
                <p className="text-xs text-muted-foreground/80 leading-relaxed">
                  AIOS enables autonomous multi-agent AI collaboration. Chat with agents and build together.
                </p>
              </div>
            </div>
          </ScrollArea>
        </div>
      </div>
      <Toaster />
    </div>
  );
}
