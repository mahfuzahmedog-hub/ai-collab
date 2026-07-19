"use client";

import { useEffect } from "react";
import { getProjectId } from "@/lib/websocket";

export default function Home() {
  useEffect(() => {
    const active = localStorage.getItem("active_project_id") || localStorage.getItem("project_id") || getProjectId();
    window.location.href = `/workspace/${encodeURIComponent(active)}?tab=chat`;
  }, []);

  return (
    <div className="flex h-screen items-center justify-center bg-dark-950 text-dark-400 text-sm">
      Loading workspace…
    </div>
  );
}
