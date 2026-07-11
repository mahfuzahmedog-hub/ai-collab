"use client";

import { Suspense, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { useStore } from "@/store";
import { MainView } from "@/features/workspace/MainView";

function WorkspacePageInner() {
  const searchParams = useSearchParams();
  const setActiveTab = useStore((s) => s.setActiveTab);
  const tab = searchParams.get("tab") || "chat";

  useEffect(() => {
    setActiveTab(tab);
  }, [tab, setActiveTab]);

  return <MainView tab={tab} />;
}

export default function WorkspacePage() {
  return (
    <Suspense fallback={<div className="flex-1 bg-dark-950" />}>
      <WorkspacePageInner />
    </Suspense>
  );
}
