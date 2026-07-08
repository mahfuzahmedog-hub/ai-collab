"use client";

import { useStore } from "@/store";
import { TaskCard } from "@/components/tasks/TaskCard";
import type { TaskStatus } from "@/types";

const columns: { label: string; statuses: TaskStatus[] }[] = [
  { label: "To Do", statuses: ["waiting", "planning", "assigned"] },
  { label: "In Progress", statuses: ["working"] },
  { label: "Review", statuses: ["review", "testing", "revision"] },
  { label: "Done", statuses: ["completed"] },
  { label: "Blocked", statuses: ["blocked"] },
];

export function TasksPage() {
  const tasks = useStore((s) => s.tasks);

  return (
    <div className="h-full overflow-x-auto">
      <div className="p-4">
        <h2 className="text-lg font-bold text-white mb-1">Task Board</h2>
        <p className="text-sm text-dark-400 mb-4">{tasks.length} total tasks</p>
      </div>

      <div className="flex gap-4 px-4 pb-4 h-[calc(100%-80px)]">
        {columns.map((col) => {
          const colTasks = tasks.filter((t) => col.statuses.includes(t.status));
          return (
            <div key={col.label} className="flex-1 min-w-[250px] bg-dark-900 rounded-lg border border-dark-700">
              <div className="p-3 border-b border-dark-700">
                <h3 className="text-sm font-semibold text-white">
                  {col.label}
                  <span className="ml-2 text-xs text-dark-400">{colTasks.length}</span>
                </h3>
              </div>
              <div className="p-2 space-y-2 overflow-y-auto" style={{ maxHeight: "calc(100% - 48px)" }}>
                {colTasks.length === 0 ? (
                  <p className="text-xs text-dark-600 text-center py-4">No tasks</p>
                ) : (
                  colTasks.map((task) => <TaskCard key={task.id} task={task} />)
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
