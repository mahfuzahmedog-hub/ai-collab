import type { Agent, Task, Message, Project, Channel, FileNode } from "@/types";
import { useStore } from "@/store";

let ws: WebSocket | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let projectId = "";
let projectInitialized = false;

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
    projectInitialized = false;
    reconnectTimer = setTimeout(() => connect(), 3000);
  };

  ws.onerror = () => {
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

export function sendChat(content: string, channel = "general") {
  send({ type: "chat", content, sender_name: "User", channel });
}

export function sendCommand(command: string, args: Record<string, any> = {}) {
  send({ type: "command", command, args });
}

function handleMessage(data: any) {
  const store = useStore.getState();

  switch (data.type) {
    case "message":
      // Only add if it matches the active channel or is general
      const activeChannel = store.activeChannel;
      if (data.channel === activeChannel || data.channel === "general") {
        store.addMessage(data as Message);
      }
      break;

    case "agent_created":
      store.addAgent(data as Agent);
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
        id: data.channel,
        name: data.name,
        project_id: data.project_id,
        unread: false,
      } as Channel);
      break;

    case "project_switched":
      store.setActiveProjectId(data.project_id);
      break;

    case "stream_chunk":
      if (data.agent_id && data.content) {
        store.setStreamingChunk({
          agentId: data.agent_id,
          content: data.content,
          done: data.done === true,
        });
      }
      break;

    case "file_changed":
      // Could refresh file tree here
      break;

    case "pong":
      break;
  }
}