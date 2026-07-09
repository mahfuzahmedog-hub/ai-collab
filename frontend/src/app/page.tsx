"use client";

import { useEffect } from "react";
import { useStore } from "@/store";
import { connect, sendCommand } from "@/lib/websocket";
import { TopBar } from "@/components/layout/TopBar";
import { LeftNav } from "@/components/layout/LeftNav";
import { AgentSidebar } from "@/components/layout/AgentSidebar";
import { Timeline } from "@/components/timeline/Timeline";

export default function Home() {
  const activeProjectId = useStore((s) => s.activeProjectId);

  useEffect(() => {
    connect();
    // Check for project in URL or localStorage
    const urlParams = new URLSearchParams(window.location.search);
    const urlProject = urlParams.get("project");
    if (urlProject) {
      sendCommand("switch_project", { project_id: urlProject });
    } else {
      const stored = localStorage.getItem("active_project_id");
      if (stored) {
        sendCommand("switch_project", { project_id: stored });
      }
    }
  }, []);

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-dark-950">
      <TopBar />
      <div className="flex flex-1 overflow-hidden">
        <LeftNav />
        <main className="flex-1 overflow-hidden min-w-0 flex flex-col">
          <Timeline />
        </main>
        <AgentSidebar />
      </div>
    </div>
  );
}