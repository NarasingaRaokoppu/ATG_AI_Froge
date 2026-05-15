/**
 * Shared TypeScript types for API requests and responses.
 */

export type Role = "user" | "assistant";
export type AttachmentType = "image" | "video" | "video_frame" | "table" | "code" | "formula" | "excel" | "docx" | "txt" | "pdf";

export interface MessageAttachment {
  attachment_type: AttachmentType;
  attachment_url?: string | null;
  content?: string | null;
  name?: string | null;
  mime_type?: string | null;
  metadata?: Record<string, unknown> | null;
}

export type MessageType =
  | "text"
  | "image"
  | "pdf"
  | "rag_response"
  | "system"
  | "upload";

export type MessageStatus = "loading" | "success" | "error";

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  attachments?: MessageAttachment[];
  message_type?: MessageType;
  created_at?: string;
  status?: MessageStatus;
  error?: string | null;
  citations?: RagCitation[];
  metadata?: Record<string, unknown> | null;
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

export type ImageStyle =
  | "photorealistic"
  | "cinematic"
  | "anime"
  | "digital-art"
  | "watercolor"
  | "minimal"
  | "none";

export type ImageAspectRatio = "1:1" | "16:9" | "9:16" | "4:3" | "3:4";

export interface GeneratedImage {
  id: string;
  user_id: string;
  thread_id: string;
  prompt: string;
  enhanced_prompt?: string | null;
  image_url: string;
  status: "pending" | "completed" | "failed" | "deleted";
  generation_time_ms?: number | null;
  style?: string | null;
  aspect_ratio?: string | null;
  model_name?: string | null;
  source_image_id?: string | null;
  created_at: string;
}

export interface ImageGenerateRequest {
  prompt: string;
  thread_id: string | null;
  style: ImageStyle;
  aspect_ratio: ImageAspectRatio;
  enhance_prompt: boolean;
}

export interface ImageGenerateResponse {
  thread_id: string;
  image: GeneratedImage;
}

export interface RagDocument {
  id: string;
  user_id: string;
  thread_id: string;
  filename: string;
  file_size: number;
  status: "queued" | "processing" | "processed" | "failed";
  upload_time: string;
  processing_time?: number | null;
  chunk_count: number;
  embedding_model: string;
}

export interface RagUploadResponse {
  document: RagDocument;
  message: string;
}

export interface RagCitation {
  document_id: string;
  filename: string;
  page_number?: number | null;
  chunk_id: string;
  content_preview: string;
  score: number;
}

export interface RagChatResponse {
  answer: string;
  confidence?: number | null;
  citations: RagCitation[];
  grounded: boolean;
}

export interface DatabaseConnection {
  id: string;
  name: string;
  host: string;
  port: number;
  database: string;
  username: string;
  has_password: boolean;
  created_at: string;
  updated_at: string;
  last_tested_at?: string | null;
}

export interface DatabaseConnectionCreateInput {
  name: string;
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
}

export interface DatabaseConnectionUpdateInput {
  name?: string;
  host?: string;
  port?: number;
  database?: string;
  username?: string;
  password?: string;
}

export interface ChartSuggestion {
  chart_type: "bar" | "line" | "pie" | "table";
  x_axis?: string | null;
  y_axis?: string | null;
}

export interface SqlQueryResponse {
  generated_sql: string;
  rows: Record<string, unknown>[];
  explanation: string;
  chart_suggestion: ChartSuggestion;
  execution_time_ms: number;
}

export interface SpreadsheetQueryResponse {
  generated_code: string;
  rows: Record<string, unknown>[];
  explanation: string;
  chart_suggestion: ChartSuggestion;
}

export interface SpreadsheetSession {
  id: string;
  thread_id: string;
  source_type: string;
  file_path?: string | null;
  original_filename?: string | null;
  mime_type?: string | null;
  google_sheet_url?: string | null;
  sheet_name?: string | null;
  dataframe_metadata?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface SpreadsheetUploadResponse {
  session: SpreadsheetSession;
  message: string;
}

export interface SpreadsheetAgentResponse {
  question: string;
  answer: string;
  explanation: string;
  generated_code: string;
  computed_result?: unknown;
  rows: Record<string, unknown>[];
  columns: string[];
  chart: ChartSuggestion;
  execution_ms: number;
  intermediate_steps: string[];
}

export interface SpreadsheetHistoryItem {
  id: string;
  thread_id: string;
  spreadsheet_session_id?: string | null;
  question: string;
  generated_code: string;
  answer_summary: string;
  execution_ms: number;
  row_count: number;
  columns?: string[] | null;
  chart_metadata?: Record<string, unknown> | null;
  created_at: string;
}

export interface SqlQueryHistoryItem {
  id: string;
  thread_id: string;
  database_connection_id?: string | null;
  source_type: string;
  user_question: string;
  generated_sql: string;
  execution_time_ms: number;
  row_count: number;
  result_columns?: string[] | null;
  assistant_summary: string;
  chart_suggestion?: Record<string, unknown> | null;
  created_at: string;
}
