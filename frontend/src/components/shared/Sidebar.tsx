import { useStore } from "@/store";
import { clsx } from "clsx";

const tabs = [
  { id: "workspace", label: "Workspace", icon: "💬" },
  { id: "agents", label: "Agents", icon: "🤖" },
  { id: "tasks", label: "Tasks", icon: "📋" },
];

const bossStatusColor: Record<string, string> = {
  idle: "bg-dark-500",
  thinking: "bg-yellow-400 animate-pulse",
  working: "bg-green-500",
  waiting: "bg-blue-500",
  blocked: "bg-red-500",
  reviewing: "bg-purple-500",
  testing: "bg-orange-500",
  done: "bg-emerald-500",
};

export function Sidebar() {
  const activeTab = useStore((s) => s.activeTab);
  const setActiveTab = useStore((s) => s.setActiveTab);
  const agents = useStore((s) => s.agents);
  const tasks = useStore((s) => s.tasks);
  const connected = useStore((s) => s.connected);
  const project = useStore((s) => s.project);

  const boss = agents.find((a) => a.role === "boss");
  const workerCount = agents.filter((a) => a.role !== "boss").length;

  return (
    <nav className="w-56 bg-dark-900 border-r border-dark-700 flex flex-col h-full">
      <div className="p-4 border-b border-dark-700">
        <h2 className="text-sm font-bold text-white tracking-wide">AI Collab</h2>
        <p className="text-xs text-dark-400 mt-0.5">Multi-Agent Workspace</p>
      </div>

      {boss && (
        <div className="mx-3 mt-3 mb-1 p-3 rounded-lg bg-yellow-500/5 border border-yellow-500/20">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-yellow-500/20 flex items-center justify-center text-base shrink-0">
              👑
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-semibold text-yellow-400 truncate">{boss.name}</span>
                <div className={clsx("w-1.5 h-1.5 rounded-full shrink-0", bossStatusColor[boss.status] || "bg-dark-500")} />
              </div>
              <p className="text-[10px] text-yellow-500/70 truncate">Engineering Manager</p>
            </div>
          </div>
          <div className="mt-2 flex gap-3 text-[10px] text-dark-400">
            <span>{workerCount} agent{workerCount !== 1 ? "s" : ""}</span>
            <span>{tasks.length} task{tasks.length !== 1 ? "s" : ""}</span>
            {project && <span className="text-dark-500 truncate">{project.title}</span>}
          </div>
        </div>
      )}

      <div className="flex-1 py-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
              activeTab === tab.id
                ? "bg-accent-600/10 text-accent-400 border-r-2 border-accent-500"
                : "text-dark-300 hover:text-white hover:bg-dark-800"
            }`}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
            {tab.id === "agents" && agents.length > 0 && (
              <span className="ml-auto text-xs bg-dark-700 px-1.5 py-0.5 rounded-full">
                {agents.length}
              </span>
            )}
            {tab.id === "tasks" && tasks.length > 0 && (
              <span className="ml-auto text-xs bg-dark-700 px-1.5 py-0.5 rounded-full">
                {tasks.length}
              </span>
            )}
          </button>
        ))}
      </div>

      <div className="p-3 border-t border-dark-700">
        <div className="flex items-center gap-1.5 mb-1">
          <div className={clsx("w-1.5 h-1.5 rounded-full", connected ? "bg-green-500" : "bg-red-500")} />
          <span className="text-[10px] text-dark-500">{connected ? "Connected" : "Offline"}</span>
        </div>
        <p className="text-[10px] text-dark-600">AI Collaboration Platform v0.1</p>
      </div>
    </nav>
  );
}
