import type { Agent, Task, Message } from "@/types";
import { useStore } from "@/store";

let ws: WebSocket | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let projectId = "";

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
  const wsEnvUrl = process.env.NEXT_PUBLIC_WS_URL || "";
  let url: string;

  if (wsEnvUrl) {
    const base = wsEnvUrl.replace(/^https?:\/\//, "").replace(/^ws[s]?:\/\//, "");
    url = `wss://${base}/ws/${pid}/user`;
  } else {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    url = `${protocol}//localhost:8000/ws/${pid}/user`;
  }

  ws = new WebSocket(url);

  ws.onopen = () => {
    useStore.getState().setConnected(true);
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
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

export function sendChat(content: string) {
  send({ type: "chat", content, sender_name: "User" });
}

export function sendCommand(command: string, args: Record<string, any> = {}) {
  send({ type: "command", command, args });
}

function handleMessage(data: any) {
  const store = useStore.getState();

  switch (data.type) {
    case "message":
      store.addMessage(data as Message);
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
      store.setProject({
        id: data.project_id,
        title: "New Project",
        description: "",
        status: "new",
        boss_agent_id: null,
        agent_ids: [],
        task_ids: [],
        user_id: "user",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
      break;

    case "status":
      if (data.agents) store.setAgents(data.agents);
      break;

    case "pong":
      break;
  }
}
