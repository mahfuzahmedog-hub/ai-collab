import type { Agent, Task, Message, Project, Channel, FileNode, Thread, ExecutionLog, Notification, Approval, LifecycleAudit, AgentStatus, ToolCall, Memory, Skill, UserProfile } from "@/types";
import { useStore } from "@/store";

let ws: WebSocket | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let pingTimer: ReturnType<typeof setInterval> | null = null;
let projectId = "";
let projectInitialized = false;
let reconnectAttempts = 0;
const MAX_RECONNECT_DELAY = 30000;
const PING_INTERVAL = 25000;

function getStorageItem(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function setStorageItem(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* localStorage not available */
  }
}

export function getProjectId(): string {
  if (projectId) return projectId;
  const stored = getStorageItem("project_id");
  if (stored) {
    projectId = stored;
    return stored;
  }
  projectId = `proj-${Math.random().toString(36).slice(2, 10)}`;
  setStorageItem("project_id", projectId);
  return projectId;
}

export function connect() {
  if (ws?.readyState === WebSocket.OPEN) return;

  const pid = getProjectId();
  const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
  const url = isLocal
    ? `ws://localhost:8000/ws/${pid}/user`
    : `wss://ai-collab-backend-j6xe.onrender.com/ws/${pid}/user`;

  ws = new WebSocket(url);

  ws.onopen = () => {
    reconnectAttempts = 0;
    if (pingTimer) clearInterval(pingTimer);
    pingTimer = setInterval(() => { if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify({type: "ping"})); }, PING_INTERVAL);
    useStore.getState().setConnected(true);
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    if (!projectInitialized) {
      projectInitialized = true;
      const storedProject = getStorageItem("active_project_id");
      if (storedProject) {
        sendCommand("switch_project", { project_id: storedProject });
      } else {
        sendCommand("create_project", { title: "My AI Project" });
      }
    }
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleMessage(data);
    } catch (e) {
      console.error("WS parse error:", e);
    }
  };

  ws.onclose = () => {
    useStore.getState().setConnected(false);
    if (pingTimer) { clearInterval(pingTimer); pingTimer = null; }
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), MAX_RECONNECT_DELAY);
    reconnectAttempts++;
    reconnectTimer = setTimeout(() => connect(), delay);
  };

  ws.onerror = (err) => {
    console.error("WS error:", err);
    ws?.close();
  };
}

export function disconnect() {
  if (reconnectTimer) clearTimeout(reconnectTimer);
  ws?.close();
  ws = null;
}

export function send(data: Record<string, any>) {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(data));
  }
}

export function sendChat(content: string, channel = "general", thread_id?: string) {
  send({ type: "chat", content, sender_name: "User", channel, thread_id });
}

export function sendCommand(command: string, args: Record<string, any> = {}) {
  send({ type: "command", command, args });
}

export function sendCreateChannel(name: string, parentId?: string, type: string = "channel") {
  const id = name.toLowerCase().replace(/[^a-z0-9]/g, "-");
  sendCommand("create_channel", { id, name, parent_id: parentId, type });
}

export function sendCreateThread(parentMessageId: string, title: string, channel: string) {
  sendCommand("create_thread", { parent_message_id: parentMessageId, title, channel });
}

export function sendCreateTask(title: string, opts: { description?: string; priority?: string; assigned_to?: string } = {}) {
  sendCommand("create_task", { title, ...opts });
}

export function sendUpdateTask(taskId: string, fields: Record<string, any>) {
  sendCommand("update_task", { task_id: taskId, ...fields });
}

export function sendPauseAgent(agentId: string) {
  sendCommand("pause_agent", { agent_id: agentId });
}

export function sendResumeAgent(agentId: string) {
  sendCommand("resume_agent", { agent_id: agentId });
}

export function sendUpdateAgent(agentId: string, data: Record<string, any>) {
  sendCommand("update_agent", { agent_id: agentId, ...data });
}

export function sendRemoveAgent(agentId: string) {
  sendCommand("remove_agent", { agent_id: agentId });
}

export function sendMarkNotificationRead(notificationId: string) {
  sendCommand("mark_notification_read", { notification_id: notificationId });
}

export function sendReadFile(path: string) {
  sendCommand("read_file", { path });
}

export function sendWriteFile(path: string, content: string) {
  sendCommand("write_file", { path, content });
}

export function sendEditMessage(messageId: string, content: string) {
  sendCommand("edit_message", { message_id: messageId, content });
}

export function sendDeleteMessage(messageId: string) {
  sendCommand("delete_message", { message_id: messageId });
}

function handleMessage(data: any) {
  const store = useStore.getState();

  switch (data.type) {
    case "message":
      // Store ALL messages regardless of channel/thread; Timeline & ThreadView
      // filter by active channel/thread for display. Prevents agent messages on
      // other channels from being silently dropped.
      store.addMessage(data as Message);
      break;

    case "message_edited":
      store.updateMessage(data.message_id, data.content);
      break;

    case "message_deleted":
      store.removeMessage(data.message_id);
      break;

    case "agent_created":
      store.addAgent(data as Agent);
      break;

    case "agent_updated":
      if (data.id) store.updateAgent(data.id, data as Partial<Agent>);
      break;

    case "agent_removed":
      store.removeAgent(data.agent_id);
      break;

    case "task_created":
      store.addTask(data as unknown as Task);
      break;

    case "task_updated":
      store.updateTask(data.id, data);
      break;

    case "task_list":
      if (data.tasks) store.setTasks(data.tasks as Task[]);
      break;

    case "file_content":
      if (typeof data.path === "string") store.setFileContent(data.path, data.content ?? "");
      break;

    case "notification_read":
      if (data.notification_id) store.markNotificationRead(data.notification_id);
      break;

    case "project_created":
      store.setActiveProjectId(data.project_id);
      setStorageItem("active_project_id", data.project_id);
      sendCommand("load_project", { project_id: data.project_id });
      break;

    case "status":
      if (data.agents) store.setAgents(data.agents);
      break;

    case "message_history":
      if (data.messages) store.setMessages(data.messages as Message[]);
      break;

    case "project_data":
      if (data.project) {
        store.setProject(data.project as Project);
        store.setActiveProjectId(data.project.id);
        setStorageItem("active_project_id", data.project.id);
      } else {
        sendCommand("create_project", { title: "My AI Project" });
      }
      break;

    case "file_tree":
      if (data.files) store.setFiles(data.files as FileNode[]);
      break;

    case "channel_created":
      store.addChannel({
        id: data.id || data.channel,
        name: data.name,
        project_id: data.project_id,
        parent_id: data.parent_id,
        type: data.channel_type || "channel",
        sort_order: data.sort_order || 0,
        unread: false,
      } as Channel);
      break;

    case "channel_tree":
      if (data.channels) store.setChannelsTree(data.channels as Channel[]);
      break;

    case "channel_renamed":
      store.updateChannel(data.id, { name: data.name });
      break;

    case "channel_moved":
      store.updateChannel(data.id, { parent_id: data.parent_id ?? undefined });
      break;

    case "channel_deleted":
      store.removeChannels((data.ids as string[]) || (data.id ? [data.id] : []));
      break;

    case "thread_created":
      store.addThread(data as unknown as Thread);
      break;

    case "thread_list":
      if (data.threads) store.setThreads(data.threads as Thread[]);
      break;

    case "agent_retired":
      store.removeAgent(data.agent_id);
      break;

    case "project_updated":
      if (data.project) store.setProject(data.project as Project);
      break;

    case "project_switched":
      store.setActiveProjectId(data.project_id);
      break;

    case "execution_logs":
      if (data.logs) store.setExecutionLogs(data.logs as ExecutionLog[]);
      break;

    case "execution_log":
      store.addExecutionLog(data as unknown as ExecutionLog);
      break;

    case "lifecycle_state_changed":
      if (data.agent_id && data.to_state) {
        store.updateAgentStatus(data.agent_id, data.to_state as AgentStatus);
        store.addLifecycleAudit(data as unknown as LifecycleAudit);
      }
      break;

    case "lifecycle_audit_list":
      if (data.audits) store.setLifecycleAudits(data.audits as LifecycleAudit[]);
      break;

    case "notification_list":
      if (data.notifications) store.setNotifications(data.notifications as Notification[]);
      break;

    case "notification":
      store.addNotification(data as unknown as Notification);
      break;

    case "approval_list":
      if (data.approvals) store.setApprovals(data.approvals as Approval[]);
      break;

    case "approval_created":
    case "approval_updated":
      store.upsertApproval(data as unknown as Approval);
      break;

    case "stream_chunk":
      if (data.agent_id) {
        store.setStreamingChunk({
          agentId: data.agent_id,
          content: data.content ?? "",
          done: data.done === true,
        });
      }
      break;

    case "file_changed":
      sendCommand("load_project", { project_id: getProjectId() });
      break;

    case "tool_call_start":
      store.addToolCall({
        id: data.tool_call_id,
        agent_id: data.agent_id,
        agent_name: data.agent_name || "",
        tool_name: data.tool_name,
        arguments: data.arguments || "",
        status: "running",
        started_at: new Date().toISOString(),
      } as ToolCall);
      break;

    case "tool_call_result":
      store.updateToolCall(data.tool_call_id, {
        result: (data.result || "").slice(0, 500),
        status: data.error ? "failed" : "completed",
        completed_at: new Date().toISOString(),
      });
      break;

    case "memory_list":
      if (data.memories) store.setMemories(data.memories as Memory[]);
      break;

    case "skill_list":
      if (data.skills) store.setSkills(data.skills as Skill[]);
      break;

    case "user_profile":
      if (data.profile) store.setUserProfile(data.profile as UserProfile);
      break;

    case "pong":
      break;
  }
}