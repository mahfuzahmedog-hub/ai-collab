"use client";

import { Suspense, useEffect } from "react";
import { connect } from "@/lib/websocket";
import { WorkspaceShell } from "@/features/workspace/WorkspaceShell";

export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Single WebSocket connection for the whole workspace lifetime.
  useEffect(() => {
    connect();
  }, []);

  return (
    <Suspense fallback={<div className="h-screen bg-dark-950" />}>
      <WorkspaceShell>{children}</WorkspaceShell>
    </Suspense>
  );
}
