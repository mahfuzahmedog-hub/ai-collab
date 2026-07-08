import { create } from "zustand";
import type { Agent, Task, Message, Project, AgentStatus } from "@/types";

interface AppState {
  project: Project | null;
  agents: Agent[];
  tasks: Task[];
  messages: Message[];
  connected: boolean;
  darkMode: boolean;
  activeTab: string;

  setProject: (p: Project) => void;
  setAgents: (a: Agent[]) => void;
  addAgent: (a: Agent) => void;
  updateAgentStatus: (id: string, status: AgentStatus) => void;
  removeAgent: (id: string) => void;
  setTasks: (t: Task[]) => void;
  addTask: (t: Task) => void;
  updateTask: (id: string, data: Partial<Task>) => void;
  addMessage: (m: Message) => void;
  setConnected: (c: boolean) => void;
  toggleDarkMode: () => void;
  setActiveTab: (t: string) => void;
}

export const useStore = create<AppState>((set) => ({
  project: null,
  agents: [],
  tasks: [],
  messages: [],
  connected: false,
  darkMode: true,
  activeTab: "workspace",

  setProject: (p) => set({ project: p }),
  setAgents: (a) => set({ agents: a }),
  addAgent: (a) => set((s) => ({ agents: [...s.agents, a] })),
  updateAgentStatus: (id, status) =>
    set((s) => ({
      agents: s.agents.map((a) => (a.id === id ? { ...a, status } : a)),
    })),
  removeAgent: (id) =>
    set((s) => ({ agents: s.agents.filter((a) => a.id !== id) })),
  setTasks: (t) => set({ tasks: t }),
  addTask: (t) => set((s) => ({ tasks: [...s.tasks, t] })),
  updateTask: (id, data) =>
    set((s) => ({
      tasks: s.tasks.map((t) => (t.id === id ? { ...t, ...data } : t)),
    })),
  addMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
  setConnected: (c) => set({ connected: c }),
  toggleDarkMode: () => set((s) => ({ darkMode: !s.darkMode })),
  setActiveTab: (t) => set({ activeTab: t }),
}));
