"use client";

import { useEffect } from "react";
import { Command } from "cmdk";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useStore } from "@/store";
import {
  MessageSquare,
  CheckSquare,
  Bot,
  Folder,
  Activity,
  Hash,
  LayoutDashboard,
} from "lucide-react";

export function CommandPalette() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const commandPaletteOpen = useStore((s) => s.commandPaletteOpen);
  const setCommandPaletteOpen = useStore((s) => s.setCommandPaletteOpen);
  const channels = useStore((s) => s.channels);
  const agents = useStore((s) => s.agents);
  const tasks = useStore((s) => s.tasks);
  const setActiveChannel = useStore((s) => s.setActiveChannel);
  const setActiveAgentProfile = useStore((s) => s.setActiveAgentProfile);

  // workspaceId from the route path /workspace/{id}
  const workspaceMatch = pathname.match(/^\/workspace\/([^/]+)/);
  const workspaceId = workspaceMatch ? workspaceMatch[1] : null;

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCommandPaletteOpen(!useStore.getState().commandPaletteOpen);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [setCommandPaletteOpen]);

  const close = () => setCommandPaletteOpen(false);

  const goToTab = (tab: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("tab", tab);
    const base = workspaceId ? `/workspace/${workspaceId}` : "/workspace";
    router.push(`${base}?${params.toString()}`);
    close();
  };

  const openChannel = (id: string) => {
    setActiveChannel(id);
    goToTab("chat");
  };

  const openAgent = (id: string) => {
    setActiveAgentProfile(id);
    close();
  };

  return (
    <Command.Dialog
      open={commandPaletteOpen}
      onOpenChange={setCommandPaletteOpen}
      label="Command Palette"
      overlayClassName="fixed inset-0 z-50 bg-black/50"
      contentClassName="fixed left-1/2 top-[15vh] -translate-x-1/2 z-[60] w-full max-w-xl"
      className="w-full bg-dark-900 border border-dark-700 rounded-lg shadow-2xl overflow-hidden"
    >
      <Command.Input
        placeholder="Type a command or search…"
        className="w-full bg-dark-950 border-b border-dark-700 px-4 py-3 text-white placeholder:text-dark-500 outline-none"
      />
      <Command.List className="max-h-[50vh] overflow-y-auto p-2">
        <Command.Empty className="text-dark-500 text-sm p-4 text-center">
          No results found.
        </Command.Empty>

        <Command.Group
          heading="Go to"
          className="text-xs text-dark-500 [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
        >
          <PaletteItem icon={<MessageSquare size={15} />} onSelect={() => goToTab("chat")}>
            Chat
          </PaletteItem>
          <PaletteItem icon={<CheckSquare size={15} />} onSelect={() => goToTab("tasks")}>
            Tasks
          </PaletteItem>
          <PaletteItem icon={<Bot size={15} />} onSelect={() => goToTab("agents")}>
            Agents
          </PaletteItem>
          <PaletteItem icon={<Folder size={15} />} onSelect={() => goToTab("files")}>
            Files
          </PaletteItem>
          <PaletteItem icon={<Activity size={15} />} onSelect={() => goToTab("activity")}>
            Activity
          </PaletteItem>
        </Command.Group>

        <Command.Group
          heading="Channels"
          className="text-xs text-dark-500 [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
        >
          {channels.map((c) => (
            <PaletteItem
              key={c.id}
              icon={<Hash size={15} />}
              value={`channel ${c.name}`}
              onSelect={() => openChannel(c.id)}
            >
              {c.name}
            </PaletteItem>
          ))}
        </Command.Group>

        <Command.Group
          heading="Agents"
          className="text-xs text-dark-500 [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
        >
          {agents.map((a) => (
            <PaletteItem
              key={a.id}
              icon={<Bot size={15} />}
              value={`agent ${a.name} ${a.role}`}
              onSelect={() => openAgent(a.id)}
            >
              {a.display_name || a.name}
            </PaletteItem>
          ))}
        </Command.Group>

        <Command.Group
          heading="Tasks"
          className="text-xs text-dark-500 [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
        >
          {tasks.map((t) => (
            <PaletteItem
              key={t.id}
              icon={<CheckSquare size={15} />}
              value={`task ${t.title}`}
              onSelect={() => goToTab("tasks")}
            >
              {t.title}
            </PaletteItem>
          ))}
        </Command.Group>

        <Command.Group
          heading="Actions"
          className="text-xs text-dark-500 [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
        >
          <PaletteItem
            icon={<LayoutDashboard size={15} />}
            value="open dashboard"
            onSelect={() => {
              router.push("/dashboard");
              close();
            }}
          >
            Open Dashboard
          </PaletteItem>
        </Command.Group>
      </Command.List>
    </Command.Dialog>
  );
}

function PaletteItem({
  icon,
  children,
  value,
  onSelect,
}: {
  icon: React.ReactNode;
  children: React.ReactNode;
  value?: string;
  onSelect: () => void;
}) {
  return (
    <Command.Item
      value={typeof value === "string" ? value : String(children)}
      onSelect={onSelect}
      className="flex items-center gap-2 px-2 py-2 text-sm text-dark-300 rounded-md cursor-pointer data-[selected=true]:bg-primary-600/20 data-[selected=true]:text-white"
    >
      <span className="text-dark-400">{icon}</span>
      {children}
    </Command.Item>
  );
}
