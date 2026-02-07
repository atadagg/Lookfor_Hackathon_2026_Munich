export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ThreadSummary {
  conversation_id: string;
  customer_email: string;
  customer_name: string;
  status: string;
  current_workflow: string | null;
  workflow_step: string | null;
  is_escalated: boolean;
  routed_agent: string;
  intent: string;
  first_message: string;
  created_at: string;
  updated_at: string;
}

export interface MessageAttachment {
  url: string;
  filename?: string;
  content_type?: string;
}

export interface ThreadMessage {
  role: string;
  content: string;
  direction: string;
  created_at: string;
  attachments?: MessageAttachment[];
}

export interface ThreadDetail {
  conversation_id: string;
  status: string;
  current_workflow: string | null;
  workflow_step: string | null;
  is_escalated: boolean;
  escalated_at: string | null;
  messages: ThreadMessage[];
}

export interface ToolTrace {
  name: string;
  inputs: Record<string, unknown>;
  output: Record<string, unknown>;
  timestamp?: string;
  duration_ms?: number;
  metadata?: {
    success?: boolean;
    has_error?: boolean;
    exception?: string;
    [key: string]: unknown;
  };
}

/** One turn in the conversation: which agent ran and its traces. */
export interface AgentTurnRecord {
  agent: string;
  intent?: string;
  current_workflow?: string;
  workflow_step?: string;
  tool_traces: ToolTrace[];
}

export interface ThreadState {
  conversation_id: string;
  messages: Array<{ role: string; content: string }>;
  customer_info: Record<string, string>;
  intent: string;
  routed_agent: string;
  current_workflow: string;
  workflow_step: string;
  is_escalated: boolean;
  /** Per-turn history so UI can show which agent handled each turn (e.g. wismo → refund). */
  agent_turn_history?: AgentTurnRecord[];
  escalation_summary?: Record<string, unknown>;
  internal_data?: {
    tool_traces?: ToolTrace[];
    [key: string]: unknown;
  };
  slots?: Record<string, unknown>;
  [key: string]: unknown;
}

export async function fetchThreads(): Promise<ThreadSummary[]> {
  const res = await fetch(`${API_URL}/threads`);
  if (!res.ok) throw new Error("Failed to fetch threads");
  return res.json();
}

export async function fetchThread(id: string): Promise<ThreadDetail> {
  const res = await fetch(`${API_URL}/thread/${id}`);
  if (!res.ok) throw new Error("Failed to fetch thread");
  return res.json();
}

export async function fetchThreadState(id: string): Promise<ThreadState> {
  const res = await fetch(`${API_URL}/thread/${id}/state`);
  if (!res.ok) throw new Error("Failed to fetch thread state");
  return res.json();
}

export interface AttachmentInput {
  filename?: string;
  content_type?: string;
  data: string; // base64-encoded
}

export interface SendMessagePayload {
  conversation_id: string;
  user_id: string;
  channel: string;
  customer_email: string;
  first_name: string;
  last_name: string;
  shopify_customer_id: string;
  message: string;
  attachments?: AttachmentInput[];
}

export async function sendMessage(payload: SendMessagePayload) {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to send message");
  return res.json();
}
