"use client";

import { useEffect } from "react";
import { useStore } from "@/store";
import { connect, getProjectId, sendCommand } from "@/lib/websocket";
import { Sidebar } from "@/components/shared/Sidebar";
import { Workspace } from "@/app/workspace/page";
import { AgentsPage } from "@/app/agents/page";
import { TasksPage } from "@/app/tasks/page";
import { Header } from "@/components/shared/Header";

export default function Home() {
  const activeTab = useStore((s) => s.activeTab);
  const connected = useStore((s) => s.connected);

  useEffect(() => {
    const pid = getProjectId();
    connect();
    sendCommand("create_project", { title: "My Project", description: "New AI collaboration project" });
  }, []);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 overflow-hidden">
          {activeTab === "workspace" && <Workspace />}
          {activeTab === "agents" && <AgentsPage />}
          {activeTab === "tasks" && <TasksPage />}
        </main>
      </div>
      <div className="fixed bottom-4 right-4 z-50">
        <div className={`w-3 h-3 rounded-full ${connected ? "bg-green-500" : "bg-red-500"}`} title={connected ? "Connected" : "Disconnected"} />
      </div>
    </div>
  );
}
