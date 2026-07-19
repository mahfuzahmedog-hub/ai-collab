"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Paperclip, Send } from "lucide-react";
import clsx from "clsx";
import { useStore } from "@/store";
import { send } from "@/lib/websocket";

interface MessageComposerProps {
  channel: string;
  disabled?: boolean;
  placeholder?: string;
}

const MIN_H = 44;
const MAX_H = 160;

export function MessageComposer({
  channel,
  disabled,
  placeholder = "Message...",
}: MessageComposerProps) {
  const agents = useStore((s) => s.agents);
  const [value, setValue] = useState("");
  const [mentionQuery, setMentionQuery] = useState<string | null>(null);
  const [mentionIdx, setMentionIdx] = useState(0);
  const [attachments, setAttachments] = useState<{name: string; data: string; type: string}[]>([]);
  const taRef = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const matches = useMemo(() => {
    if (mentionQuery === null) return [];
    const q = mentionQuery.toLowerCase();
    return agents
      .filter((a) => a.name.toLowerCase().includes(q))
      .slice(0, 6);
  }, [mentionQuery, agents]);

  // Auto-grow
  useEffect(() => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(Math.max(ta.scrollHeight, MIN_H), MAX_H)}px`;
  }, [value]);

  function handleChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    const v = e.target.value;
    setValue(v);
    const word = v.slice(0, e.target.selectionStart).split(/\s/).pop() || "";
    if (word.startsWith("@")) setMentionQuery(word.slice(1));
    else setMentionQuery(null);
    setMentionIdx(0);
  }

  function insertMention(name: string) {
    const ta = taRef.current;
    if (!ta) return;
    const pos = ta.selectionStart;
    const before = value.slice(0, pos).replace(/@\S*$/, `@${name} `);
    const after = value.slice(pos);
    setValue(before + after);
    setMentionQuery(null);
    requestAnimationFrame(() => ta.focus());
  }

  function handleSend() {
    if ((!value.trim() && attachments.length === 0) || disabled) return;
    const mentions = [...value.matchAll(/@([^\s@]+)/g)].map((m) => m[1]);
    const payload: Record<string, unknown> = { type: "chat", content: value.trim(), sender_name: "User", channel, mentions };
    if (attachments.length > 0) payload.attachments = attachments;
    send(payload);
    setValue("");
    setAttachments([]);
    setMentionQuery(null);
  }

  function handleAttach(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) return;
    const reader = new FileReader();
    reader.onload = () => {
      setAttachments([...attachments, { name: file.name, data: reader.result as string, type: "image" }]);
    };
    reader.readAsDataURL(file);
    e.target.value = "";
  }

  function removeAttachment(idx: number) {
    setAttachments(attachments.filter((_, i) => i !== idx));
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (mentionQuery !== null && matches.length > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setMentionIdx((i) => (i + 1) % matches.length);
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setMentionIdx((i) => (i - 1 + matches.length) % matches.length);
        return;
      }
      if (e.key === "Enter" || e.key === "Tab") {
        e.preventDefault();
        insertMention(matches[mentionIdx].name);
        return;
      }
      if (e.key === "Escape") {
        e.preventDefault();
        setMentionQuery(null);
        return;
      }
    }
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="relative">
      {mentionQuery !== null && matches.length > 0 && (
        <div className="absolute bottom-full left-0 mb-1 w-56 bg-dark-800 border border-dark-700 rounded-lg overflow-hidden shadow-lg z-10">
          {matches.map((a, i) => (
            <button
              key={a.id}
              type="button"
              onMouseDown={(e) => {
                e.preventDefault();
                insertMention(a.name);
              }}
              className={clsx(
                "w-full text-left px-3 py-1.5 text-sm text-dark-100 hover:bg-dark-700",
                i === mentionIdx && "bg-dark-700"
              )}
            >
              <span className="text-white">{a.name}</span>
              <span className="text-dark-500 text-xs ml-2">{a.role}</span>
            </button>
          ))}
        </div>
      )}
      <div className="flex items-end gap-2">
        <div className="relative flex-1">
          {attachments.length > 0 && (
            <div className="flex gap-2 mb-2 flex-wrap">
              {attachments.map((att, i) => (
                <div key={i} className="relative group">
                  <img src={att.data} alt={att.name} className="h-16 w-16 object-cover rounded border border-dark-600" />
                  <button type="button" onClick={() => removeAttachment(i)} className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-red-600 text-white rounded-full text-xs leading-none hidden group-hover:flex items-center justify-center">&times;</button>
                </div>
              ))}
            </div>
          )}
          <textarea
            ref={taRef}
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-white placeholder-dark-500 resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
            style={{ minHeight: MIN_H, maxHeight: MAX_H }}
          />
          <div className="absolute left-2 bottom-1.5 group">
            <button type="button" onClick={() => fileRef.current?.click()} className="text-dark-400 hover:text-dark-200" aria-label="Attach file">
              <Paperclip className="w-4 h-4" />
            </button>
            <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleAttach} />
          </div>
        </div>
        <button
          type="button"
          onClick={handleSend}
          disabled={!value.trim() || disabled}
          className="p-2 bg-primary-600 text-white rounded-lg hover:bg-primary-500 disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
      <div className="mt-1 text-xs text-dark-500">Markdown supported</div>
    </div>
  );
}
