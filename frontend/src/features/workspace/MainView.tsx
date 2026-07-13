"use client";

import { Timeline } from "@/components/timeline/Timeline";
import { AgentsPage } from "@/components/agents/Panel";
import { KanbanBoard } from "@/features/tasks/KanbanBoard";
import { FilesTab } from "@/features/files/FilesTab";
import { ActivityTab } from "@/features/activity/ActivityTab";
import { MemoryPanel } from "@/features/knowledge/MemoryPanel";
import { SkillPanel } from "@/features/knowledge/SkillPanel";
import { useStore } from "@/store";

export function MainView({ tab }: { tab: string }) {
  switch (tab) {
    case "tasks":
      return <KanbanBoard />;
    case "agents":
      return <AgentsPage />;
    case "files":
      return <FilesTab />;
    case "activity":
      return <ActivityTab />;
    case "knowledge":
      return <KnowledgeView />;
    case "chat":
    default:
      return <Timeline />;
  }
}

function KnowledgeView() {
  const activeTab = useStore((s) => s.activeTab);
  return (
    <div className="flex h-full">
      <div className="flex-1 border-r border-dark-700">
        <MemoryPanel />
      </div>
      <div className="flex-1">
        <SkillPanel />
      </div>
    </div>
  );
}
