"use client";

import { useEffect } from "react";
import { useStore } from "@/store";
import { connect } from "@/lib/websocket";
import { TopBar } from "@/components/layout/TopBar";
import { LeftNav } from "@/components/layout/LeftNav";
import { AgentSidebar } from "@/components/layout/AgentSidebar";
import { Dashboard } from "@/components/layout/Dashboard";
import { Timeline } from "@/components/timeline/Timeline";
import { AgentsPage } from "@/components/agents/Panel";
import { TasksPage } from "@/components/tasks/Panel";

export default function Home() {
  const activeTab = useStore((s) => s.activeTab);

  useEffect(() => {
    connect();
  }, []);

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <TopBar />
      <div className="flex flex-1 overflow-hidden">
        <LeftNav />
        <AgentSidebar />
        <main className="flex-1 overflow-hidden min-w-0">
          {activeTab === "workspace" && <Timeline />}
          {activeTab === "agents" && <AgentsPage />}
          {activeTab === "tasks" && <TasksPage />}
        </main>
        <Dashboard />
      </div>
    </div>
  );
}
