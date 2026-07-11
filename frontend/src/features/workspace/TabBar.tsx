"use client";

import { useEffect } from "react";
import { useSearchParams, usePathname, useRouter } from "next/navigation";
import { useStore } from "@/store";
import { clsx } from "clsx";

const TABS = [
  { id: "chat", label: "Chat" },
  { id: "tasks", label: "Tasks" },
  { id: "agents", label: "Agents" },
  { id: "files", label: "Files" },
  { id: "activity", label: "Activity" },
];

const SOON = [
  { id: "knowledge", label: "Knowledge" },
  { id: "tools", label: "Tools" },
  { id: "workflows", label: "Workflows" },
];

// Switching tabs only updates the ?tab= query on the same route segment, so the
// workspace layout (and the single WebSocket connection) stays mounted.
export function TabBar() {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();
  const setActiveTab = useStore((s) => s.setActiveTab);

  const activeTab = searchParams.get("tab") || "chat";

  useEffect(() => {
    setActiveTab(activeTab);
  }, [activeTab, setActiveTab]);

  const go = (tab: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("tab", tab);
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  };

  return (
    <nav
      role="tablist"
      aria-label="Workspace views"
      className="h-10 flex-shrink-0 border-b border-dark-700 bg-dark-900 flex items-center px-2 gap-1 overflow-x-auto"
    >
      {TABS.map((t) => (
        <button
          key={t.id}
          role="tab"
          aria-selected={activeTab === t.id}
          aria-current={activeTab === t.id ? "page" : undefined}
          onClick={() => go(t.id)}
          className={clsx(
            "px-3 py-1.5 text-sm rounded-md transition-colors whitespace-nowrap focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500",
            activeTab === t.id
              ? "bg-primary-600/20 text-white"
              : "text-dark-300 hover:bg-dark-700 hover:text-white"
          )}
        >
          {t.label}
        </button>
      ))}
      <span className="w-px h-5 bg-dark-700 mx-1" />
      {SOON.map((t) => (
        <span
          key={t.id}
          title="Coming soon"
          aria-disabled="true"
          className="px-3 py-1.5 text-sm rounded-md text-dark-600 cursor-not-allowed whitespace-nowrap"
        >
          {t.label} <span className="text-[10px]">Soon</span>
        </span>
      ))}
    </nav>
  );
}
