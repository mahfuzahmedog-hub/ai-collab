import { useStore } from "@/store";
import { clsx } from "clsx";

export function Header() {
  const project = useStore((s) => s.project);
  const connected = useStore((s) => s.connected);
  const agents = useStore((s) => s.agents);
  const tasks = useStore((s) => s.tasks);

  const boss = agents.find((a) => a.role === "boss");
  const workerCount = agents.filter((a) => a.role !== "boss").length;

  return (
    <header className="h-12 border-b border-dark-700 flex items-center px-4 gap-3 bg-dark-900">
      <h1 className="text-sm font-semibold text-white truncate">
        {project?.title || "AI Collaboration Platform"}
      </h1>

      {boss && (
        <div className="hidden sm:flex items-center gap-2 ml-4 pl-4 border-l border-dark-700">
          <span className="text-xs text-yellow-400 font-medium">{boss.name}</span>
          <div className={clsx("w-1.5 h-1.5 rounded-full", {
            "bg-yellow-400 animate-pulse": boss.status === "thinking",
            "bg-green-500": boss.status === "working" || boss.status === "idle",
            "bg-red-500": boss.status === "blocked",
            "bg-dark-500": !boss.status,
          })} />
          <span className="text-[10px] text-dark-400 capitalize">{boss.status}</span>
        </div>
      )}

      <div className="flex items-center gap-3 ml-auto">
        {agents.length > 0 && (
          <div className="hidden md:flex items-center gap-3 text-[10px] text-dark-400">
            <span>{workerCount} agent{workerCount !== 1 ? "s" : ""}</span>
            <span>{tasks.length} task{tasks.length !== 1 ? "s" : ""}</span>
          </div>
        )}
        <div className="flex items-center gap-1.5">
          <div className={`w-2 h-2 rounded-full ${connected ? "bg-green-500" : "bg-red-500"}`} />
          <span className="text-xs text-dark-300">{connected ? "Live" : "Offline"}</span>
        </div>
      </div>
    </header>
  );
}
