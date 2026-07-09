import { useState, useRef, KeyboardEvent } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import {
  Send,
  AtSign,
  Code,
  Link,
  Smile,
  Paperclip,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface Agent {
  _id: string;
  name: string;
  emoji?: string;
}

interface MessageInputProps {
  onSend: (content: string, contentType?: string) => void;
  agents: Agent[];
  disabled?: boolean;
  placeholder?: string;
}

export function MessageInput({ onSend, agents, disabled, placeholder }: MessageInputProps) {
  const [content, setContent] = useState("");
  const [showMentions, setShowMentions] = useState(false);
  const [mentionSearch, setMentionSearch] = useState("");
  const [selectedMentionIndex, setSelectedMentionIndex] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const filteredAgents = mentionSearch
    ? agents.filter((a) =>
        a.name.toLowerCase().includes(mentionSearch.toLowerCase()),
      )
    : agents;

  const handleSend = () => {
    const trimmed = content.trim();
    if (!trimmed || disabled) return;

    // Check if it's a code block
    const isCode = trimmed.startsWith("```") || trimmed.startsWith("`");
    onSend(trimmed, isCode ? "code" : "text");
    setContent("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (showMentions) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedMentionIndex((prev) =>
          Math.min(prev + 1, filteredAgents.length - 1),
        );
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedMentionIndex((prev) => Math.max(prev - 1, 0));
        return;
      }
      if (e.key === "Enter" && filteredAgents.length > 0) {
        e.preventDefault();
        insertMention(filteredAgents[selectedMentionIndex]);
        return;
      }
      if (e.key === "Escape") {
        setShowMentions(false);
        return;
      }
    }

    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleChange = (value: string) => {
    setContent(value);

    // Check for @mention trigger
    const cursorPos = textareaRef.current?.selectionStart ?? value.length;
    const textBeforeCursor = value.slice(0, cursorPos);
    const atMatch = textBeforeCursor.match(/@(\w*)$/);

    if (atMatch) {
      setShowMentions(true);
      setMentionSearch(atMatch[1]);
      setSelectedMentionIndex(0);
    } else {
      setShowMentions(false);
    }
  };

  const insertMention = (agent: Agent) => {
    const cursorPos = textareaRef.current?.selectionStart ?? content.length;
    const textBeforeCursor = content.slice(0, cursorPos);
    const textAfterCursor = content.slice(cursorPos);
    const atMatch = textBeforeCursor.match(/@(\w*)$/);

    if (atMatch) {
      const newContent =
        textBeforeCursor.slice(0, atMatch.index) +
        `@${agent.name} ` +
        textAfterCursor;
      setContent(newContent);
      setShowMentions(false);
      textareaRef.current?.focus();
    }
  };

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + "px";
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    handleChange(e.target.value);
    adjustTextareaHeight();
  };

  return (
    <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="px-4 py-3">
        {/* Mentions dropdown */}
        {showMentions && filteredAgents.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            className="mb-2 rounded-lg border bg-popover p-1 shadow-lg max-h-40 overflow-y-auto"
          >
            <p className="px-2 py-1 text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
              Agents
            </p>
            {filteredAgents.map((agent, i) => (
              <button
                key={agent._id}
                onClick={() => insertMention(agent)}
                className={cn(
                  "w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors",
                  i === selectedMentionIndex
                    ? "bg-accent text-accent-foreground"
                    : "hover:bg-accent/50",
                )}
              >
                <span>{agent.emoji ?? "🤖"}</span>
                <span className="font-medium">{agent.name}</span>
                <span className="text-xs text-muted-foreground ml-auto">
                  @{agent.name.toLowerCase()}
                </span>
              </button>
            ))}
          </motion.div>
        )}

        {/* Input area */}
        <div className="flex items-end gap-2">
          <div className="relative flex-1">
            <Textarea
              ref={textareaRef}
              value={content}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              placeholder={placeholder ?? `Message #team-chat`}
              disabled={disabled}
              rows={1}
              className="min-h-[44px] max-h-[200px] resize-none pr-10 py-3 text-sm rounded-xl bg-muted/50 border-muted-foreground/20 focus-visible:ring-primary/30"
            />
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className={cn(
                      "absolute right-1.5 bottom-1.5 h-8 w-8 rounded-lg transition-all",
                      content.trim()
                        ? "text-primary hover:text-primary hover:bg-primary/10"
                        : "text-muted-foreground/40",
                    )}
                    onClick={() => {
                      textareaRef.current?.focus();
                      const pos = textareaRef.current?.selectionStart ?? content.length;
                      const newContent =
                        content.slice(0, pos) + "@" + content.slice(pos);
                      setContent(newContent);
                    }}
                  >
                    <AtSign className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="top">
                  <p>Mention an agent (@)</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>

          <div className="flex items-center gap-1">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-10 w-10 rounded-xl text-muted-foreground/60 hover:text-muted-foreground"
                  >
                    <Paperclip className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="top">
                  <p>Attach file</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <Button
              onClick={handleSend}
              disabled={!content.trim() || disabled}
              size="icon"
              className="h-10 w-10 rounded-xl bg-primary hover:bg-primary/90 transition-all active:scale-95"
            >
              {disabled ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        <p className="mt-1.5 text-[10px] text-muted-foreground/50 text-center">
          Press <kbd className="px-1 py-0.5 rounded bg-muted font-mono text-[10px]">Enter</kbd> to send,{" "}
          <kbd className="px-1 py-0.5 rounded bg-muted font-mono text-[10px]">Shift+Enter</kbd> for new line,{" "}
          <kbd className="px-1 py-0.5 rounded bg-muted font-mono text-[10px]">@</kbd> to mention an agent
        </p>
      </div>
    </div>
  );
}
