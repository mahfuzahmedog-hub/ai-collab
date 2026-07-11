"use client";

import { useState } from "react";
import { Pencil, Trash2, Check, X } from "lucide-react";
import type { Message } from "@/types";
import { sendEditMessage, sendDeleteMessage } from "@/lib/websocket";

export function MessageActions({ message }: { message: Message }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(message.content);

  if (message.sender_role !== "user") return null;

  function save() {
    if (draft.trim()) sendEditMessage(message.id, draft.trim());
    setEditing(false);
  }

  if (editing) {
    return (
      <div className="mt-2">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          autoFocus
          rows={2}
          className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-white text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
        <div className="flex items-center gap-2 mt-1">
          <button
            type="button"
            onClick={save}
            className="flex items-center gap-1 text-xs text-primary-400 hover:text-primary-500"
          >
            <Check className="w-3.5 h-3.5" /> Save
          </button>
          <button
            type="button"
            onClick={() => {
              setDraft(message.content);
              setEditing(false);
            }}
            className="flex items-center gap-1 text-xs text-dark-400 hover:text-dark-300"
          >
            <X className="w-3.5 h-3.5" /> Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
      <button
        type="button"
        onClick={() => {
          setDraft(message.content);
          setEditing(true);
        }}
        className="flex items-center gap-1 text-xs text-dark-400 hover:text-primary-400"
      >
        <Pencil className="w-3.5 h-3.5" /> Edit
      </button>
      <button
        type="button"
        onClick={() => {
          if (confirm("Delete this message?")) sendDeleteMessage(message.id);
        }}
        className="flex items-center gap-1 text-xs text-dark-400 hover:text-red-400"
      >
        <Trash2 className="w-3.5 h-3.5" /> Delete
      </button>
    </div>
  );
}
