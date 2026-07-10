import { create } from "zustand";
import type { Agent, Task, Message, Project, AgentStatus, Channel, FileNode, Thread } from "@/types";

interface AppState {
  // Project state
  projects: Project[];
  activeProjectId: string | null;
  project: Project | null;

  // Channel state
  channels: Channel[];
  activeChannel: string;

  // Channel tree
  collapsedCategories: Record<string, boolean>;

  // Threads
  threads: Thread[];
  activeThread: string | null;

  // Agents, tasks, messages
  agents: Agent[];
  tasks: Task[];
  messages: Message[];

  // File tree
  files: FileNode[];

  // Streaming
  streamingChunk: { agentId: string; content: string; done: boolean } | null;

  // Connection
  connected: boolean;

  // UI state
  activeTab: string;

  // Actions
  setProjects: (p: Project[]) => void;
  setActiveProjectId: (id: string) => void;
  setProject: (p: Project) => void;
  setChannels: (c: Channel[]) => void;
  addChannel: (c: Channel) => void;
  setActiveChannel: (id: string) => void;
  setChannelsTree: (channels: Channel[]) => void;
  toggleCategory: (categoryId: string) => void;
  setThreads: (t: Thread[]) => void;
  addThread: (t: Thread) => void;
  setActiveThread: (id: string | null) => void;
  setAgents: (a: Agent[]) => void;
  addAgent: (a: Agent) => void;
  updateAgentStatus: (id: string, status: AgentStatus) => void;
  removeAgent: (id: string) => void;
  setTasks: (t: Task[]) => void;
  addTask: (t: Task) => void;
  updateTask: (id: string, data: Partial<Task>) => void;
  addMessage: (m: Message) => void;
  setMessages: (m: Message[]) => void;
  setFiles: (f: FileNode[]) => void;
  setStreamingChunk: (chunk: { agentId: string; content: string; done: boolean } | null) => void;
  setConnected: (c: boolean) => void;
  setActiveTab: (t: string) => void;
  clearProjectData: () => void;
}

export const useStore = create<AppState>((set) => ({
  projects: [],
  activeProjectId: null,
  project: null,
  channels: [],
  activeChannel: "general",
  collapsedCategories: {},
  threads: [],
  activeThread: null,
  agents: [],
  tasks: [],
  messages: [],
  files: [],
  streamingChunk: null,
  connected: false,
  activeTab: "workspace",

  setProjects: (p) => set({ projects: p }),
  setActiveProjectId: (id) => set({ activeProjectId: id }),
  setProject: (p) => set({ project: p }),
  setChannels: (c) => set({ channels: c }),
  addChannel: (c) => set((s) => ({ channels: [...s.channels, c] })),
  setActiveChannel: (id) => set({ activeChannel: id }),
  setChannelsTree: (c) => set({ channels: c }),
  toggleCategory: (categoryId) =>
    set((s) => ({
      collapsedCategories: {
        ...s.collapsedCategories,
        [categoryId]: !s.collapsedCategories[categoryId],
      },
    })),
  setThreads: (t) => set({ threads: t }),
  addThread: (t) => set((s) => ({ threads: [...s.threads, t] })),
  setActiveThread: (id) => set({ activeThread: id }),
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
  setMessages: (m) => set({ messages: m }),
  setFiles: (f) => set({ files: f }),
  setStreamingChunk: (chunk) => set({ streamingChunk: chunk }),
  setConnected: (c) => set({ connected: c }),
  setActiveTab: (t) => set({ activeTab: t }),
  clearProjectData: () =>
    set({
      agents: [],
      tasks: [],
      messages: [],
      files: [],
      channels: [],
      activeChannel: "general",
      collapsedCategories: {},
      threads: [],
      activeThread: null,
      project: null,
      streamingChunk: null,
    }),
}));