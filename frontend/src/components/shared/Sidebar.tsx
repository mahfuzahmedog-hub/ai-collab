import { useStore } from "@/store";

const tabs = [
  { id: "workspace", label: "Workspace", icon: "💬" },
  { id: "agents", label: "Agents", icon: "🤖" },
  { id: "tasks", label: "Tasks", icon: "📋" },
];

export function Sidebar() {
  const activeTab = useStore((s) => s.activeTab);
  const setActiveTab = useStore((s) => s.setActiveTab);
  const agents = useStore((s) => s.agents);
  const tasks = useStore((s) => s.tasks);

  return (
    <nav className="w-56 bg-dark-900 border-r border-dark-700 flex flex-col h-full">
      <div className="p-4 border-b border-dark-700">
        <h2 className="text-sm font-bold text-white tracking-wide">AI Collab</h2>
        <p className="text-xs text-dark-400 mt-0.5">Multi-Agent Workspace</p>
      </div>

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
        <p className="text-xs text-dark-500">AI Collaboration Platform v0.1</p>
      </div>
    </nav>
  );
}
