import { motion, AnimatePresence } from "framer-motion";
import {
  Hash,
  MessageCircle,
  Bot,
  Users,
  Plus,
  Settings,
  BotIcon,
  ChevronDown,
  ChevronRight,
  Circle,
  Search,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Badge } from "@/components/ui/badge";

interface Agent {
  _id: string;
  name: string;
  emoji?: string;
  color?: string;
  status: string;
  type: string;
}

interface Channel {
  _id: string;
  name: string;
  type: "group" | "direct" | "thread";
  agentIds: string[];
  isDefault?: boolean;
}

interface ChannelSidebarProps {
  agents: Agent[];
  channels: Channel[];
  selectedChannelId: string | null;
  selectedDirectAgentId?: string | null;
  onSelectChannel: (channelId: string) => void;
  onSelectDirectMessage: (agentId: string) => void;
  onNewProject?: () => void;
  unreadCount?: number;
}

export function ChannelSidebar({
  agents,
  channels,
  selectedChannelId,
  selectedDirectAgentId,
  onSelectChannel,
  onSelectDirectMessage,
  onNewProject,
  unreadCount = 0,
}: ChannelSidebarProps) {
  const groupChannels = channels.filter((c) => c.type === "group");
  const directChannels = channels.filter((c) => c.type === "direct");

  const agentStatusColor = (status: string) => {
    switch (status) {
      case "idle": return "bg-green-500";
      case "working": return "bg-blue-500";
      case "reviewing": return "bg-yellow-500";
      case "blocked": return "bg-red-500";
      case "error": return "bg-red-600";
      case "retired": return "bg-gray-500";
      default: return "bg-gray-400";
    }
  };

  const getAgentFromDirectChannel = (channel: Channel) => {
    if (channel.agentIds.length > 0) {
      return agents.find((a) => a._id === channel.agentIds[0]);
    }
    return null;
  };

  return (
    <div className="flex h-full bg-sidebar border-r border-sidebar-border">
      {/* Server Bar - narrow left strip */}
      <div className="w-[52px] flex flex-col items-center py-3 gap-2 bg-sidebar-accent/50 border-r border-sidebar-border">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-10 w-10 rounded-2xl bg-primary/10 hover:bg-primary/20 hover:rounded-xl transition-all duration-200"
                onClick={onNewProject}
              >
                <BotIcon className="h-5 w-5 text-primary" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">
              <p>AIOS Home</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        <div className="w-8 h-px bg-sidebar-border" />

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-10 w-10 rounded-xl hover:bg-sidebar-accent text-sidebar-foreground/60 hover:text-sidebar-foreground"
              >
                <Users className="h-5 w-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">
              <p>Team</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-10 w-10 rounded-xl hover:bg-sidebar-accent text-sidebar-foreground/60 hover:text-sidebar-foreground"
              >
                <Search className="h-5 w-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">
              <p>Search</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        <div className="flex-1" />

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-10 w-10 rounded-xl hover:bg-sidebar-accent text-sidebar-foreground/60 hover:text-sidebar-foreground"
              >
                <Settings className="h-5 w-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">
              <p>Settings</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {/* Channels & Agents List */}
      <div className="flex-1 flex flex-col">
        {/* Server Name */}
        <div className="h-12 flex items-center px-4 border-b border-sidebar-border shadow-sm">
          <div className="flex items-center gap-2 flex-1">
            <BotIcon className="h-4 w-4 text-primary" />
            <span className="font-semibold text-sm text-sidebar-foreground truncate">AIOS</span>
          </div>
          {unreadCount > 0 && (
            <Badge variant="destructive" className="h-5 min-w-5 px-1 text-[10px]">
              {unreadCount}
            </Badge>
          )}
        </div>

        <ScrollArea className="flex-1">
          <div className="p-2 space-y-4">
            {/* Group Chat Channels */}
            <div>
              <div className="flex items-center justify-between px-2 py-1">
                <div className="flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/50">
                  <ChevronDown className="h-3 w-3" />
                  Channels
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-4 w-4 rounded-sm opacity-0 group-hover:opacity-100 hover:opacity-100"
                >
                  <Plus className="h-3 w-3" />
                </Button>
              </div>

              <div className="space-y-0.5 mt-1">
                {groupChannels.length === 0 && (
                  <div className="px-2 py-1 text-xs text-sidebar-foreground/40 italic">
                    No channels yet
                  </div>
                )}
                {groupChannels.map((channel) => (
                  <button
                    key={channel._id}
                    onClick={() => onSelectChannel(channel._id)}
                    className={cn(
                      "w-full flex items-center gap-1.5 px-2 py-1.5 rounded-md text-sm transition-all duration-150",
                      selectedChannelId === channel._id
                        ? "bg-sidebar-primary text-sidebar-primary-foreground"
                        : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground",
                    )}
                  >
                    <Hash className="h-4 w-4 shrink-0" />
                    <span className="truncate">{channel.name === "general" ? "Team Chat" : channel.name}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Direct Messages */}
            <div>
              <div className="flex items-center px-2 py-1">
                <div className="flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/50">
                  <ChevronDown className="h-3 w-3" />
                  Agents
                </div>
              </div>

              <div className="space-y-0.5 mt-1">
                {agents.length === 0 && (
                  <div className="px-2 py-1 text-xs text-sidebar-foreground/40 italic">
                    No agents yet
                  </div>
                )}
                {agents.map((agent) => (
                  <button
                    key={agent._id}
                    onClick={() => {
                      // Find or use the direct channel for this agent
                      const directChannel = directChannels.find((dc) =>
                        dc.agentIds.includes(agent._id)
                      );
                      if (directChannel) {
                        onSelectChannel(directChannel._id);
                      } else {
                        onSelectDirectMessage(agent._id);
                      }
                    }}
                    className={cn(
                      "w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-all duration-150 group",
                      selectedDirectAgentId === agent._id
                        ? "bg-sidebar-primary text-sidebar-primary-foreground"
                        : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground",
                    )}
                  >
                    <div className="relative shrink-0">
                      <span className="text-base">{agent.emoji ?? "🤖"}</span>
                      <Circle
                        className={cn(
                          "h-2 w-2 absolute -bottom-0.5 -right-0.5 fill-current",
                          agentStatusColor(agent.status),
                          selectedDirectAgentId === agent._id ? "text-sidebar-primary" : "text-sidebar",
                        )}
                      />
                    </div>
                    <div className="flex-1 flex items-center justify-between min-w-0">
                      <span className="truncate">{agent.name}</span>
                      <div className="flex items-center gap-1">
                        <MessageCircle className="h-3 w-3 opacity-0 group-hover:opacity-60 transition-opacity shrink-0" />
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
