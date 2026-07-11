"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { useStore } from "@/store";
import { sendCreateTask, sendUpdateTask } from "@/lib/websocket";
import type { Task, TaskPriority } from "@/types";

interface TaskDrawerProps {
  open: boolean;
  onClose: () => void;
  task?: Task | null;
}

const priorities: TaskPriority[] = ["low", "medium", "high", "critical"];

export function TaskDrawer({ open, onClose, task }: TaskDrawerProps) {
  const agents = useStore((s) => s.agents);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<TaskPriority>("medium");
  const [assignedTo, setAssignedTo] = useState<string>("");

  useEffect(() => {
    if (!open) return;
    setTitle(task?.title ?? "");
    setDescription(task?.description ?? "");
    setPriority(task?.priority ?? "medium");
    setAssignedTo(task?.assigned_to ?? "");
  }, [open, task]);

  const handleSave = () => {
    const trimmed = title.trim();
    if (!trimmed) return;
    if (task) {
      sendUpdateTask(task.id, {
        title: trimmed,
        description,
        priority,
        assigned_to: assignedTo || null,
      });
    } else {
      sendCreateTask(trimmed, {
        description,
        priority,
        assigned_to: assignedTo || undefined,
      });
    }
    onClose();
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            className="fixed inset-0 z-40 bg-black/50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.aside
            className="fixed right-0 top-0 z-50 flex h-full w-full max-w-md flex-col border-l border-dark-700 bg-dark-900 shadow-xl"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "tween", duration: 0.2 }}
          >
            <div className="flex items-center justify-between border-b border-dark-700 p-4">
              <h2 className="text-sm font-semibold text-white">
                {task ? "Edit Task" : "New Task"}
              </h2>
              <button
                onClick={onClose}
                className="text-dark-400 hover:text-white"
                aria-label="Close"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="flex-1 space-y-4 overflow-y-auto p-4">
              <div>
                <label className="mb-1 block text-xs font-medium text-dark-400">Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Task title"
                  autoFocus
                  className="w-full rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-white placeholder-dark-500 focus:border-primary-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium text-dark-400">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe the task"
                  rows={5}
                  className="w-full resize-none rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-white placeholder-dark-500 focus:border-primary-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium text-dark-400">Priority</label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as TaskPriority)}
                  className="w-full rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-white focus:border-primary-500 focus:outline-none"
                >
                  {priorities.map((p) => (
                    <option key={p} value={p} className="capitalize">
                      {p}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-1 block text-xs font-medium text-dark-400">Assignee</label>
                <select
                  value={assignedTo}
                  onChange={(e) => setAssignedTo(e.target.value)}
                  className="w-full rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-white focus:border-primary-500 focus:outline-none"
                >
                  <option value="">Unassigned</option>
                  {agents.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.display_name || a.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 border-t border-dark-700 p-4">
              <button
                onClick={onClose}
                className="rounded-lg border border-dark-700 px-4 py-2 text-sm text-dark-300 hover:bg-dark-800 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={!title.trim()}
                className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Save
              </button>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
