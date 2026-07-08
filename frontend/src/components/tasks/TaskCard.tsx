import type { Task } from "@/types";
import { clsx } from "clsx";

const statusColors: Record<string, string> = {
  waiting: "bg-dark-600",
  planning: "bg-blue-600",
  assigned: "bg-yellow-600",
  working: "bg-green-600",
  blocked: "bg-red-600",
  review: "bg-purple-600",
  testing: "bg-orange-600",
  revision: "bg-pink-600",
  completed: "bg-emerald-600",
  rejected: "bg-red-800",
  cancelled: "bg-dark-800",
};

const priorityColors: Record<string, string> = {
  critical: "border-red-500",
  high: "border-orange-500",
  medium: "border-yellow-500",
  low: "border-blue-500",
};

export function TaskCard({ task }: { task: Task }) {
  return (
    <div className={clsx(
      "bg-dark-800 border border-dark-700 rounded-lg p-3 border-l-4",
      priorityColors[task.priority] || "border-l-dark-600"
    )}>
      <div className="flex items-center gap-2 mb-1">
        <div className={clsx("w-2 h-2 rounded-full shrink-0", statusColors[task.status] || "bg-dark-500")} />
        <h3 className="text-sm font-medium text-white truncate">{task.title}</h3>
      </div>

      {task.description && (
        <p className="text-xs text-dark-400 mt-1 line-clamp-2">{task.description}</p>
      )}

      <div className="flex items-center gap-2 mt-2 text-xs text-dark-500">
        <span className="capitalize">{task.status.replace(/_/g, " ")}</span>
        <span>•</span>
        <span className="capitalize">{task.priority}</span>
        {task.depends_on.length > 0 && (
          <>
            <span>•</span>
            <span>{task.depends_on.length} dep{(task.depends_on.length || 1) > 1 ? "s" : ""}</span>
          </>
        )}
      </div>
    </div>
  );
}
