"use client";

import { Timeline } from "@/components/timeline/Timeline";
import { AgentsPage } from "@/components/agents/Panel";
import { KanbanBoard } from "@/features/tasks/KanbanBoard";
import { FilesTab } from "@/features/files/FilesTab";
import { ActivityTab } from "@/features/activity/ActivityTab";

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
    case "chat":
    default:
      return <Timeline />;
  }
}
