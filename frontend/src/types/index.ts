export interface Agent {
  id: string;
  name: string;
  display_name?: string;
  mission?: string;
  version?: string;
  is_permanent?: boolean;
  role: string;
  personality: string;
  emoji?: string;
  color?: string;
  max_tokens?: number;
  channel?: string;
  status: AgentStatus;
  current_task_id: string | null;
  skills: string[];
  project_id: string;
  provider: string;
  model: string;
  created_at: string;
  last_active: string;
}

export type AgentStatus =
  | "creating" | "initializing" | "idle" | "assigned" | "planning"
  | "waiting_for_dependencies" | "researching" | "thinking" | "working"
  | "collaborating" | "reviewing" | "awaiting_user_approval" | "approved"
  | "executing" | "testing" | "completed" | "archived" | "blocked" | "paused"
  | "retrying" | "failed" | "error" | "retired";

export interface Task {
  id: string;
  project_id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  assigned_to: string | null;
  assigned_by: string | null;
  dependencies: string[];
  depends_on: string[];
  subtasks: string[];
  parent_task_id: string | null;
  reviews: Review[];
  tests: any[];
  artifacts: string[];
  estimated_hours: number | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export type TaskStatus =
  | "waiting" | "planning" | "assigned" | "working"
  | "blocked" | "review" | "testing" | "revision"
  | "completed" | "rejected" | "cancelled";

export type TaskPriority = "critical" | "high" | "medium" | "low";

export interface Review {
  reviewer_id: string;
  status: "pending" | "approved" | "rejected";
  comments?: string;
  reason?: string;
  submitted_at?: string;
  timestamp?: string;
}

export interface Message {
  id: string;
  project_id: string;
  sender_id: string;
  sender_name: string;
  sender_role: string;
  content: string;
  msg_type: "chat" | "task_update" | "review" | "system" | "file";
  channel: string;
  thread_id?: string | null;
  reply_to: string | null;
  mentions: string[];
  attachments: any[];
  metadata: Record<string, any>;
  timestamp: string;
}

export interface Channel {
  id: string;
  name: string;
  project_id: string;
  parent_id?: string;
  type?: "category" | "channel";
  sort_order?: number;
  children?: Channel[];
  unread: boolean;
}

export interface Thread {
  id: string;
  project_id: string;
  channel: string;
  parent_message_id: string;
  title: string;
  created_by: string;
  created_at: string;
  messages?: Message[];
}

export interface FileNode {
  name: string;
  path: string;
  type: "file" | "directory";
  children?: FileNode[];
  size?: number;
  modified?: number;
}

export interface Project {
  id: string;
  title: string;
  description: string;
  status: string;
  boss_agent_id: string | null;
  agent_ids: string[];
  task_ids: string[];
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface ExecutionLog {
  id: string;
  project_id: string;
  agent_id?: string | null;
  agent_name: string;
  action: string;
  model: string;
  provider: string;
  status: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_usd: number;
  latency_ms: number;
  input_preview: string;
  output_preview: string;
  created_at: string;
}

export interface Notification {
  id: string;
  project_id: string;
  user_id: string;
  type: "mention" | "task" | "approval" | "system";
  title: string;
  body: string;
  link?: string | null;
  read: boolean;
  created_at: string;
}

export interface Approval {
  id: string;
  project_id: string;
  agent_id?: string | null;
  agent_name: string;
  action: string;
  description: string;
  payload: Record<string, any>;
  status: "pending" | "approved" | "rejected";
  created_at: string;
}

export interface LifecycleAudit {
  id: string;
  project_id: string;
  agent_id?: string | null;
  agent_name: string;
  from_state: string;
  to_state: string;
  reason: string;
  created_at: string;
}

export interface WSMessage {
  type: string;
  [key: string]: any;
}
