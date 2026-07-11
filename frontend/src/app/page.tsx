"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getProjectId } from "@/lib/websocket";

// Workspace resolver: route into the persistent shell. The WS create_project
// flow auto-creates the project on connect, so just route into the id.
export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const active =
      localStorage.getItem("active_project_id") ||
      localStorage.getItem("project_id") ||
      getProjectId();
    router.replace(`/workspace/${encodeURIComponent(active)}?tab=chat`);
  }, [router]);

  return (
    <div className="flex h-screen items-center justify-center bg-dark-950 text-dark-400 text-sm">
      Loading workspace…
    </div>
  );
}
