"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useStore } from "@/store";
import { sendMarkNotificationRead } from "@/lib/websocket";
import { clsx } from "clsx";
import {
  Bell,
  AtSign,
  CheckSquare,
  ShieldCheck,
  Settings,
  CheckCheck,
  X,
} from "lucide-react";
import type { Notification } from "@/types";

type FilterType = "all" | Notification["type"];

const TYPE_ICON: Record<Notification["type"], React.ReactNode> = {
  mention: <AtSign size={15} />,
  task: <CheckSquare size={15} />,
  approval: <ShieldCheck size={15} />,
  system: <Settings size={15} />,
};

const FILTERS: { id: FilterType; label: string }[] = [
  { id: "all", label: "All" },
  { id: "mention", label: "Mention" },
  { id: "task", label: "Task" },
  { id: "approval", label: "Approval" },
  { id: "system", label: "System" },
];

function timeAgo(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const diff = Date.now() - then;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h`;
  return `${Math.floor(hrs / 24)}d`;
}

export function NotificationCenter() {
  const notificationsOpen = useStore((s) => s.notificationsOpen);
  const setNotificationsOpen = useStore((s) => s.setNotificationsOpen);
  const notifications = useStore((s) => s.notifications);
  const markNotificationRead = useStore((s) => s.markNotificationRead);
  const markAllNotificationsRead = useStore((s) => s.markAllNotificationsRead);
  const setActiveChannel = useStore((s) => s.setActiveChannel);

  const [filter, setFilter] = useState<FilterType>("all");

  useEffect(() => {
    if (notificationsOpen) {
      const unread = notifications.filter((n) => !n.read);
      if (unread.length > 0) {
        unread.forEach((n) => sendMarkNotificationRead(n.id));
        markAllNotificationsRead();
      }
    }
  }, [notificationsOpen]);

  const visible = [...notifications]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .filter((n) => filter === "all" || n.type === filter);

  const close = () => setNotificationsOpen(false);

  const onNotificationClick = (n: Notification) => {
    sendMarkNotificationRead(n.id);
    markNotificationRead(n.id);
    if (n.link && n.link.startsWith("channel://")) {
      setActiveChannel(n.link.replace("channel://", ""));
    }
    close();
  };

  const onMarkAll = () => {
    notifications
      .filter((n) => !n.read)
      .forEach((n) => sendMarkNotificationRead(n.id));
    markAllNotificationsRead();
  };

  return (
    <AnimatePresence>
      {notificationsOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={close} />
          <motion.div
            className="fixed top-14 right-4 z-50 w-80 max-h-[70vh] bg-dark-900 border border-dark-700 rounded-lg shadow-2xl flex flex-col"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.15 }}
          >
            <div className="flex items-center justify-between p-3 border-b border-dark-700">
              <div className="flex items-center gap-2 text-white font-medium text-sm">
                <Bell size={15} /> Notifications
              </div>
              <button
                onClick={close}
                className="text-dark-400 hover:text-white transition-colors"
                title="Close"
              >
                <X size={16} />
              </button>
            </div>

            <div className="flex flex-wrap gap-1 p-2 border-b border-dark-700">
              {FILTERS.map((f) => (
                <button
                  key={f.id}
                  onClick={() => setFilter(f.id)}
                  className={clsx(
                    "text-xs px-2 py-1 rounded-full transition-colors",
                    filter === f.id
                      ? "bg-primary-600 text-white"
                      : "bg-dark-800 text-dark-300 hover:text-white"
                  )}
                >
                  {f.label}
                </button>
              ))}
              <button
                onClick={onMarkAll}
                className="ml-auto flex items-center gap-1 text-xs text-primary-400 hover:text-primary-300 transition-colors"
                title="Mark all as read"
              >
                <CheckCheck size={14} /> Mark all read
              </button>
            </div>

            <div className="flex-1 overflow-y-auto">
              {visible.length === 0 ? (
                <div className="p-6 text-center text-dark-500 text-sm">No notifications</div>
              ) : (
                visible.map((n) => (
                  <button
                    key={n.id}
                    onClick={() => onNotificationClick(n)}
                    className={clsx(
                      "w-full text-left px-3 py-2 border-b border-dark-800 hover:bg-dark-800 transition-colors flex gap-2",
                      !n.read && "bg-primary-600/5"
                    )}
                  >
                    <div
                      className={clsx(
                        "mt-0.5 flex-shrink-0",
                        n.type === "mention"
                          ? "text-blue-400"
                          : n.type === "task"
                          ? "text-green-400"
                          : n.type === "approval"
                          ? "text-yellow-400"
                          : "text-dark-400"
                      )}
                    >
                      {TYPE_ICON[n.type]}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-white font-medium truncate flex-1">
                          {n.title}
                        </span>
                        {!n.read && (
                          <span className="w-2 h-2 rounded-full bg-primary-500 flex-shrink-0" />
                        )}
                      </div>
                      <div className="text-xs text-dark-400 truncate">{n.body}</div>
                      <div className="text-[10px] text-dark-600 mt-0.5">{timeAgo(n.created_at)}</div>
                    </div>
                  </button>
                ))
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
