"use client";

import { WorkspaceSwitcher } from "./WorkspaceSwitcher";

export function ServerRail() {
  return (
    <div className="w-[52px] flex-shrink-0 bg-dark-950 border-r border-dark-700 flex flex-col items-center py-2 gap-2">
      <WorkspaceSwitcher />
    </div>
  );
}
