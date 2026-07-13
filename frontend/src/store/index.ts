import { create } from "zustand";
import type { Agent, Task, Message, Project, AgentStatus, Channel, FileNode, Thread, ExecutionLog, Notification, Approval, LifecycleAudit, ToolCall, Memory, Skill, UserProfile } from "@/types";

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

  // Observability / ops
  executionLogs: ExecutionLog[];
  notifications: Notification[];
  approvals: Approval[];
  lifecycleAudits: LifecycleAudit[];

  // Tool calls
  toolCalls: ToolCall[];

  // Knowledge
  memories: Memory[];
  skills: Skill[];
  userProfile: UserProfile | null;

  // Streaming
  streamingChunk: { agentId: string; content: string; done: boolean } | null;

  // Connection
  connected: boolean;

  // UI state
  activeTab: string;

  addToolCall: (tc: ToolCall) => void;
  updateToolCall: (id: string, data: Partial<ToolCall>) => void;
  setMemories: (m: Memory[]) => void;
  setSkills: (s: Skill[]) => void;
  setUserProfile: (p: UserProfile | null) => void;

  // Workspace shell UI (M1)
  panelSizes: Record<string, number>;
  leftCollapsed: boolean;
  rightCollapsed: boolean;
  commandPaletteOpen: boolean;

  // Files (M2)
  fileContents: Record<string, string>;
  selectedFile: string | null;

  // Notifications / agent profile UI (M4/M5)
  notificationsOpen: boolean;
  activeAgentProfile: string | null;

  // Actions
  setProjects: (p: Project[]) => void;
  setActiveProjectId: (id: string) => void;
  setProject: (p: Project) => void;
  setChannels: (c: Channel[]) => void;
  addChannel: (c: Channel) => void;
  updateChannel: (id: string, data: Partial<Channel>) => void;
  removeChannels: (ids: string[]) => void;
  setActiveChannel: (id: string) => void;
  setChannelsTree: (channels: Channel[]) => void;
  toggleCategory: (categoryId: string) => void;
  setThreads: (t: Thread[]) => void;
  addThread: (t: Thread) => void;
  setActiveThread: (id: string | null) => void;
  setAgents: (a: Agent[]) => void;
  addAgent: (a: Agent) => void;
  updateAgent: (id: string, data: Partial<Agent>) => void;
  updateAgentStatus: (id: string, status: AgentStatus) => void;
  removeAgent: (id: string) => void;
  setTasks: (t: Task[]) => void;
  addTask: (t: Task) => void;
  updateTask: (id: string, data: Partial<Task>) => void;
  addMessage: (m: Message) => void;
  updateMessage: (id: string, content: string) => void;
  removeMessage: (id: string) => void;
  setMessages: (m: Message[]) => void;
  setFiles: (f: FileNode[]) => void;
  setExecutionLogs: (l: ExecutionLog[]) => void;
  addExecutionLog: (l: ExecutionLog) => void;
  setNotifications: (n: Notification[]) => void;
  addNotification: (n: Notification) => void;
  markNotificationRead: (id: string) => void;
  setApprovals: (a: Approval[]) => void;
  upsertApproval: (a: Approval) => void;
  setLifecycleAudits: (a: LifecycleAudit[]) => void;
  addLifecycleAudit: (a: LifecycleAudit) => void;
  setStreamingChunk: (chunk: { agentId: string; content: string; done: boolean } | null) => void;
  setConnected: (c: boolean) => void;
  setActiveTab: (t: string) => void;
  setPanelSize: (key: string, size: number) => void;
  toggleLeftCollapsed: () => void;
  toggleRightCollapsed: () => void;
  setCommandPaletteOpen: (v: boolean) => void;
  setFileContent: (path: string, content: string) => void;
  setSelectedFile: (path: string | null) => void;
  setNotificationsOpen: (v: boolean) => void;
  markAllNotificationsRead: () => void;
  setActiveAgentProfile: (id: string | null) => void;
  clearProjectData: () => void;
}

function flattenChannels(nodes: Channel[]): Channel[] {
  const out: Channel[] = [];
  const walk = (list: Channel[]) => {
    for (const n of list) {
      const { children, ...rest } = n as Channel & { children?: Channel[] };
      out.push(rest as Channel);
      if (children && children.length) walk(children);
    }
  };
  walk(nodes || []);
  return out;
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
  executionLogs: [],
  notifications: [],
  approvals: [],
  lifecycleAudits: [],
  toolCalls: [],
  memories: [],
  skills: [],
  userProfile: null,
  streamingChunk: null,
  connected: false,
  activeTab: "workspace",
  panelSizes: {},
  leftCollapsed: false,
  rightCollapsed: false,
  commandPaletteOpen: false,
  fileContents: {},
  selectedFile: null,
  notificationsOpen: false,
  activeAgentProfile: null,

  addToolCall: (tc) =>
    set((s) => ({ toolCalls: s.toolCalls.some((x) => x.id === tc.id) ? s.toolCalls.map((x) => x.id === tc.id ? { ...x, ...tc } : x) : [...s.toolCalls, tc] })),
  updateToolCall: (id, data) =>
    set((s) => ({ toolCalls: s.toolCalls.map((tc) => (tc.id === id ? { ...tc, ...data } : tc)) })),
  setMemories: (m) => set({ memories: m }),
  setSkills: (s) => set({ skills: s }),
  setUserProfile: (p) => set({ userProfile: p }),
  setProjects: (p) => set({ projects: p }),
  setActiveProjectId: (id) => set({ activeProjectId: id }),
  setProject: (p) => set({ project: p }),
  setChannels: (c) => set({ channels: c }),
  addChannel: (c) =>
    set((s) => (s.channels.some((x) => x.id === c.id) ? {} : { channels: [...s.channels, c] })),
  updateChannel: (id, data) =>
    set((s) => ({ channels: s.channels.map((c) => (c.id === id ? { ...c, ...data } : c)) })),
  removeChannels: (ids) =>
    set((s) => {
      const gone = new Set(ids);
      return {
        channels: s.channels.filter((c) => !gone.has(c.id)),
        activeChannel: gone.has(s.activeChannel) ? "general" : s.activeChannel,
        activeThread: null,
      };
    }),
  setActiveChannel: (id) => set({ activeChannel: id }),
  setChannelsTree: (c) => set({ channels: flattenChannels(c) }),
  toggleCategory: (categoryId) =>
    set((s) => ({
      collapsedCategories: {
        ...s.collapsedCategories,
        [categoryId]: !s.collapsedCategories[categoryId],
      },
    })),
  setThreads: (t) => set({ threads: t }),
  addThread: (t) => set((s) => (s.threads.some((x) => x.id === t.id) ? {} : { threads: [...s.threads, t] })),
  setActiveThread: (id) => set({ activeThread: id }),
  setAgents: (a) => set({ agents: a }),
  addAgent: (a) => set((s) => ({ agents: [...s.agents, a] })),
  updateAgent: (id, data) =>
    set((s) => ({ agents: s.agents.map((a) => (a.id === id ? { ...a, ...data } : a)) })),
  updateAgentStatus: (id, status) =>
    set((s) => ({
      agents: s.agents.map((a) => (a.id === id ? { ...a, status } : a)),
    })),
  removeAgent: (id) =>
    set((s) => ({ agents: s.agents.filter((a) => a.id !== id) })),
  setTasks: (t) => set({ tasks: t }),
  addTask: (t) => set((s) => (s.tasks.some((x) => x.id === t.id) ? {} : { tasks: [...s.tasks, t] })),
  updateTask: (id, data) =>
    set((s) => ({
      tasks: s.tasks.map((t) => (t.id === id ? { ...t, ...data } : t)),
    })),
  addMessage: (m) =>
    set((s) => (s.messages.some((x) => x.id === m.id) ? {} : { messages: [...s.messages, m] })),
  updateMessage: (id, content) =>
    set((s) => ({
      messages: s.messages.map((m) => (m.id === id ? { ...m, content } : m)),
    })),
  removeMessage: (id) =>
    set((s) => ({ messages: s.messages.filter((m) => m.id !== id) })),
  setMessages: (m) => set({ messages: m }),
  setFiles: (f) => set({ files: f }),
  setExecutionLogs: (l) => set({ executionLogs: l }),
  addExecutionLog: (l) => set((s) => ({ executionLogs: [l, ...s.executionLogs].slice(0, 500) })),
  setNotifications: (n) => set({ notifications: n }),
  addNotification: (n) => set((s) => ({ notifications: [n, ...s.notifications].slice(0, 200) })),
  markNotificationRead: (id) =>
    set((s) => ({ notifications: s.notifications.map((n) => (n.id === id ? { ...n, read: true } : n)) })),
  setApprovals: (a) => set({ approvals: a }),
  upsertApproval: (a) =>
    set((s) => ({
      approvals: s.approvals.some((x) => x.id === a.id)
        ? s.approvals.map((x) => (x.id === a.id ? a : x))
        : [a, ...s.approvals],
    })),
  setLifecycleAudits: (a) => set({ lifecycleAudits: a }),
  addLifecycleAudit: (a) => set((s) => ({ lifecycleAudits: [a, ...s.lifecycleAudits].slice(0, 500) })),
  setStreamingChunk: (chunk) => set({ streamingChunk: chunk }),
  setConnected: (c) => set({ connected: c }),
  setActiveTab: (t) => set({ activeTab: t }),
  setPanelSize: (key, size) => set((s) => ({ panelSizes: { ...s.panelSizes, [key]: size } })),
  toggleLeftCollapsed: () => set((s) => ({ leftCollapsed: !s.leftCollapsed })),
  toggleRightCollapsed: () => set((s) => ({ rightCollapsed: !s.rightCollapsed })),
  setCommandPaletteOpen: (v) => set({ commandPaletteOpen: v }),
  setFileContent: (path, content) => set((s) => ({ fileContents: { ...s.fileContents, [path]: content } })),
  setSelectedFile: (path) => set({ selectedFile: path }),
  setNotificationsOpen: (v) => set({ notificationsOpen: v }),
  markAllNotificationsRead: () =>
    set((s) => ({ notifications: s.notifications.map((n) => ({ ...n, read: true })) })),
  setActiveAgentProfile: (id) => set({ activeAgentProfile: id }),
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
      executionLogs: [],
      notifications: [],
      approvals: [],
      lifecycleAudits: [],
      streamingChunk: null,
    }),
}));