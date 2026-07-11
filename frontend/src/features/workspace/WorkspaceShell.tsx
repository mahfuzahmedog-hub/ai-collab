"use client";

import { useStore } from "@/store";
import { PanelGroup, Panel, PanelResizeHandle } from "react-resizable-panels";
import { LeftNav } from "@/components/layout/LeftNav";
import { AgentSidebar } from "@/components/layout/AgentSidebar";
import { ApprovalDialog } from "@/components/approvals/ApprovalDialog";
import { WorkspaceHeader } from "./WorkspaceHeader";
import { TabBar } from "./TabBar";
import { StatusBar } from "./StatusBar";
import { ServerRail } from "./ServerRail";
import { AgentProfile } from "@/features/agents/AgentProfile";
import { NotificationCenter } from "@/features/notifications/NotificationCenter";
import { CommandPalette } from "@/features/search/CommandPalette";

// Persistent shell: the layout renders this once and never unmounts while
// switching tabs (children swap via the route's ?tab= query).
export function WorkspaceShell({ children }: { children: React.ReactNode }) {
  const leftCollapsed = useStore((s) => s.leftCollapsed);
  const rightCollapsed = useStore((s) => s.rightCollapsed);
  const toggleLeftCollapsed = useStore((s) => s.toggleLeftCollapsed);
  const toggleRightCollapsed = useStore((s) => s.toggleRightCollapsed);

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-dark-950 text-white">
      <WorkspaceHeader />
      <TabBar />

      <div className="flex flex-1 overflow-hidden min-h-0">
        <ServerRail />

        {/* Left nav — collapsible, hidden below md */}
        {leftCollapsed ? (
          <button
            onClick={toggleLeftCollapsed}
            className="hidden md:flex w-10 flex-shrink-0 bg-dark-900 border-r border-dark-700 items-center justify-center text-dark-400 hover:text-white"
            title="Expand navigation"
          >
            »
          </button>
        ) : (
          <div className="hidden md:block flex-shrink-0">
            <LeftNav />
          </div>
        )}

        {/* Resizable main + right context region */}
        <PanelGroup direction="horizontal" className="flex-1 min-w-0">
          <Panel defaultSize={75} minSize={30} className="min-w-0">
            <main className="h-full overflow-hidden min-w-0 flex flex-col bg-dark-950">
              {children}
            </main>
          </Panel>

          <PanelResizeHandle className="w-1 bg-dark-700 hover:bg-primary-600 transition-colors hidden md:block" />

          <Panel defaultSize={25} minSize={15} collapsible className="hidden md:flex min-w-0">
            {rightCollapsed ? (
              <button
                onClick={toggleRightCollapsed}
                className="w-full h-full bg-dark-900 border-l border-dark-700 text-dark-400 hover:text-white flex items-start justify-center pt-3"
                title="Expand panel"
              >
                «
              </button>
            ) : (
              <div className="h-full flex flex-col min-w-0 w-full">
                <div className="flex items-center justify-end p-1 border-b border-dark-700">
                  <button
                    onClick={toggleRightCollapsed}
                    className="text-dark-400 hover:text-white text-xs px-2"
                    title="Collapse panel"
                  >
                    «
                  </button>
                </div>
                <div className="flex-1 min-h-0">
                  <AgentSidebar />
                </div>
              </div>
            )}
          </Panel>
        </PanelGroup>
      </div>

      <StatusBar />
      <ApprovalDialog />

      {/* M4 / M5 overlays */}
      <AgentProfile />
      <NotificationCenter />
      <CommandPalette />
    </div>
  );
}
