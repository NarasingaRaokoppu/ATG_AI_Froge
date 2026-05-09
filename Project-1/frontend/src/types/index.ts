/**
 * Shared TypeScript types for API requests and responses.
 */

export type Role = "user" | "assistant";
export type AttachmentType = "image" | "video" | "video_frame" | "table" | "code" | "formula" | "excel" | "docx" | "txt";

export interface MessageAttachment {
  attachment_type: AttachmentType;
  attachment_url?: string | null;
  content?: string | null;
  name?: string | null;
  mime_type?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  attachments?: MessageAttachment[];
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
  attachment_type?: string | null;
  attachment_url?: string | null;
  attachment_metadata?: Record<string, unknown> | null;
  attachments?: MessageAttachment[];
  created_at: string;
}

export interface UploadAttachmentResponse {
  attachment_type: "image" | "video" | "excel" | "docx" | "txt";
  attachment_url: string;
  name: string;
  mime_type: string;
  size_bytes: number;
  content?: string | null;
  video_frames?: string[] | null;
}
