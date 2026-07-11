"use client";

import { useMemo, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { clsx } from "clsx";
import { Plus } from "lucide-react";
import { useStore } from "@/store";
import { sendUpdateTask } from "@/lib/websocket";
import { TaskDrawer } from "@/features/tasks/TaskDrawer";
import type { Task, TaskStatus } from "@/types";

interface Column {
  id: string;
  label: string;
  statuses: TaskStatus[];
}

// First status in each list is the representative status applied on drop.
const columns: Column[] = [
  { id: "backlog", label: "Backlog", statuses: ["waiting", "planning", "rejected"] },
  { id: "todo", label: "Todo", statuses: ["assigned"] },
  { id: "in_progress", label: "In Progress", statuses: ["working"] },
  { id: "review", label: "Review", statuses: ["review", "revision"] },
  { id: "testing", label: "Testing", statuses: ["testing"] },
  { id: "completed", label: "Completed", statuses: ["completed"] },
  { id: "blocked", label: "Blocked", statuses: ["blocked"] },
];

const statusColors: Record<string, string> = {
  waiting: "bg-dark-500",
  planning: "bg-blue-500",
  assigned: "bg-yellow-500",
  working: "bg-green-500",
  blocked: "bg-red-500",
  review: "bg-purple-500",
  testing: "bg-orange-500",
  revision: "bg-pink-500",
  completed: "bg-emerald-500",
  rejected: "bg-red-800",
  cancelled: "bg-dark-700",
};

const priorityBorder: Record<string, string> = {
  critical: "border-l-red-500",
  high: "border-l-orange-500",
  medium: "border-l-yellow-500",
  low: "border-l-blue-500",
};

function TaskCardView({ task, agentName }: { task: Task; agentName: string | null }) {
  const depCount = task.depends_on?.length ?? 0;
  return (
    <div
      className={clsx(
        "rounded-lg border border-dark-700 border-l-4 bg-dark-800 p-3",
        priorityBorder[task.priority] || "border-l-dark-600"
      )}
    >
      <div className="mb-1 flex items-center gap-2">
        <div className={clsx("h-2 w-2 shrink-0 rounded-full", statusColors[task.status] || "bg-dark-500")} />
        <h3 className="truncate text-sm font-medium text-white">{task.title}</h3>
      </div>
      <div className="mt-2 flex items-center gap-2 text-xs text-dark-500">
        <span className="truncate">{agentName ?? "Unassigned"}</span>
        {depCount > 0 && (
          <>
            <span>•</span>
            <span>{depCount} dep{depCount > 1 ? "s" : ""}</span>
          </>
        )}
      </div>
    </div>
  );
}

function SortableCard({ task, agentName, onClick }: { task: Task; agentName: string | null; onClick: () => void }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: task.id });
  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition, opacity: isDragging ? 0.4 : 1 }}
      {...attributes}
      {...listeners}
      onClick={onClick}
      className="cursor-grab active:cursor-grabbing"
    >
      <TaskCardView task={task} agentName={agentName} />
    </div>
  );
}

function ColumnView({
  column,
  tasks,
  agentName,
  onCardClick,
}: {
  column: Column;
  tasks: Task[];
  agentName: (id: string | null) => string | null;
  onCardClick: (task: Task) => void;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: column.id });
  return (
    <div className="flex w-[260px] min-w-[260px] flex-col rounded-lg border border-dark-700 bg-dark-900">
      <div className="flex items-center justify-between border-b border-dark-700 p-3">
        <h3 className="text-sm font-semibold text-white">{column.label}</h3>
        <span className="text-xs text-dark-400">{tasks.length}</span>
      </div>
      <div
        ref={setNodeRef}
        className={clsx(
          "flex-1 space-y-2 overflow-y-auto p-2 transition-colors",
          isOver && "bg-dark-800/50"
        )}
      >
        {tasks.length === 0 ? (
          <p className="py-4 text-center text-xs text-dark-600">Drop tasks here</p>
        ) : (
          tasks.map((task) => (
            <SortableCard
              key={task.id}
              task={task}
              agentName={agentName(task.assigned_to)}
              onClick={() => onCardClick(task)}
            />
          ))
        )}
      </div>
    </div>
  );
}

export function KanbanBoard() {
  const tasks = useStore((s) => s.tasks);
  const agents = useStore((s) => s.agents);

  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editTask, setEditTask] = useState<Task | null>(null);
  const [activeId, setActiveId] = useState<string | null>(null);

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  const agentName = (id: string | null): string | null => {
    if (!id) return null;
    const a = agents.find((x) => x.id === id);
    return a ? a.display_name || a.name : id;
  };

  // Map every non-cancelled task to its column; cancelled tasks are hidden.
  const tasksByColumn = useMemo(() => {
    const map: Record<string, Task[]> = {};
    for (const col of columns) map[col.id] = [];
    for (const task of tasks) {
      if (task.status === "cancelled") continue;
      const col = columns.find((c) => c.statuses.includes(task.status)) ?? columns[0];
      map[col.id].push(task);
    }
    return map;
  }, [tasks]);

  const activeTask = activeId ? tasks.find((t) => t.id === activeId) ?? null : null;

  const handleDragStart = (e: DragStartEvent) => setActiveId(String(e.active.id));

  const handleDragEnd = (e: DragEndEvent) => {
    setActiveId(null);
    const { active, over } = e;
    if (!over) return;

    const task = tasks.find((t) => t.id === String(active.id));
    if (!task) return;

    // `over.id` is either a column droppable id or a card id inside a column.
    const overId = String(over.id);
    let targetColumn = columns.find((c) => c.id === overId);
    if (!targetColumn) {
      const overTask = tasks.find((t) => t.id === overId);
      if (overTask) targetColumn = columns.find((c) => c.statuses.includes(overTask.status));
    }
    if (!targetColumn) return;

    const representative = targetColumn.statuses[0];
    if (task.status === representative) return;
    if (targetColumn.statuses.includes(task.status)) return;

    sendUpdateTask(task.id, { status: representative });
  };

  const openCreate = () => {
    setEditTask(null);
    setDrawerOpen(true);
  };

  const openEdit = (task: Task) => {
    setEditTask(task);
    setDrawerOpen(true);
  };

  return (
    <div className="flex h-full flex-col bg-dark-950">
      <div className="flex items-center justify-between p-4">
        <div>
          <h2 className="text-lg font-bold text-white">Kanban Board</h2>
          <p className="text-sm text-dark-400">
            {tasks.filter((t) => t.status !== "cancelled").length} tasks
          </p>
        </div>
        <button
          onClick={openCreate}
          className="flex items-center gap-1.5 rounded-lg bg-primary-600 px-3 py-2 text-sm font-medium text-white hover:bg-primary-500"
        >
          <Plus className="h-4 w-4" />
          New Task
        </button>
      </div>

      <DndContext
        sensors={sensors}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragCancel={() => setActiveId(null)}
      >
        <div className="flex flex-1 gap-4 overflow-x-auto px-4 pb-4">
          {columns.map((col) => (
            <ColumnView
              key={col.id}
              column={col}
              tasks={tasksByColumn[col.id]}
              agentName={agentName}
              onCardClick={openEdit}
            />
          ))}
        </div>

        <DragOverlay>
          {activeTask ? (
            <TaskCardView task={activeTask} agentName={agentName(activeTask.assigned_to)} />
          ) : null}
        </DragOverlay>
      </DndContext>

      <TaskDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} task={editTask} />
    </div>
  );
}
