"use client";

import { useEffect } from "react";
import { connect, sendCommand } from "@/lib/websocket";
import { TopBar } from "@/components/layout/TopBar";
import { LeftNav } from "@/components/layout/LeftNav";
import { AgentSidebar } from "@/components/layout/AgentSidebar";
import { Timeline } from "@/components/timeline/Timeline";
import { ApprovalDialog } from "@/components/approvals/ApprovalDialog";

export default function Home() {
  useEffect(() => {
    connect();
    // Check for project in URL
    const urlParams = new URLSearchParams(window.location.search);
    const urlProject = urlParams.get("project");
    if (urlProject) {
      sendCommand("switch_project", { project_id: urlProject });
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
      <ApprovalDialog />
    </div>
  );
}