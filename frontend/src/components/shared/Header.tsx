import { useStore } from "@/store";

export function Header() {
  const project = useStore((s) => s.project);
  const connected = useStore((s) => s.connected);

  return (
    <header className="h-12 border-b border-dark-700 flex items-center px-4 gap-3 bg-dark-900">
      <h1 className="text-sm font-semibold text-white truncate">
        {project?.title || "AI Collaboration Platform"}
      </h1>
      <div className="flex items-center gap-2 ml-auto">
        <div className="flex items-center gap-1.5">
          <div className={`w-2 h-2 rounded-full ${connected ? "bg-green-500" : "bg-red-500"}`} />
          <span className="text-xs text-dark-300">{connected ? "Live" : "Offline"}</span>
        </div>
      </div>
    </header>
  );
}
