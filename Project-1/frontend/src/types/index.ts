/**
 * Shared TypeScript types for API requests and responses.
 */

export type Role = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  /** True while this assistant message is still streaming. */
  pending?: boolean;
}

export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface Thread {
  id: string;
  title: string | null;
  created_at: string;
}

export interface MessageDTO {
  id: string;
  thread_id: string;
  role: Role;
  content: string;
  created_at: string;
}
