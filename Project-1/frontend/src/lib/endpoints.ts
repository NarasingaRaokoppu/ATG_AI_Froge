/**
 * Auth + thread + message API helpers.
 * Built on top of the centralized fetch client in `./api`.
 */

import { api } from "./api";
import type {
  GeneratedImage,
  ImageAspectRatio,
  ImageGenerateRequest,
  ImageGenerateResponse,
  ImageStyle,
  MessageDTO,
  RagChatResponse,
  RagDocument,
  RagUploadResponse,
  Thread,
  UploadAttachmentResponse,
  User,
} from "../types";

export const authApi = {
  register: (email: string, password: string) =>
    api.post<User>("/auth/register", { email, password }),
  login: (email: string, password: string) =>
    api.post<User>("/auth/login", { email, password }),
  logout: () => api.post<void>("/auth/logout"),
  me: () => api.get<User>("/auth/me"),
};

export const threadApi = {
  list: () => api.get<Thread[]>("/threads"),
  create: (title?: string | null) =>
    api.post<Thread>("/threads", { title: title ?? null }),
  rename: (threadId: string, title: string) =>
    api.patch<Thread>(`/threads/${threadId}`, { title }),
  remove: (threadId: string) => api.delete<void>(`/threads/${threadId}`),
};

export const messageApi = {
  list: (threadId: string) => api.get<MessageDTO[]>(`/messages/${threadId}`),
};

export const uploadApi = {
  uploadFile: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.postForm<UploadAttachmentResponse>("/upload", form);
  },
};

export const imageApi = {
  generate: (payload: ImageGenerateRequest) =>
    api.post<ImageGenerateResponse>("/v1/images/generate", payload),
  listByThread: (threadId: string) =>
    api.get<GeneratedImage[]>(`/v1/threads/${threadId}/images`),
  remove: (imageId: string) =>
    api.delete<{ deleted: boolean; image_id: string }>(`/v1/images/${imageId}`),
  regenerate: (payload: {
    image_id: string;
    prompt_override?: string | null;
    style?: ImageStyle;
    aspect_ratio?: ImageAspectRatio;
    enhance_prompt?: boolean;
  }) => api.post<ImageGenerateResponse>("/v1/images/regenerate", payload),
};

export const ragApi = {
  uploadPdf: (threadId: string, file: File) => {
    const form = new FormData();
    form.append("thread_id", threadId);
    form.append("file", file);
    return api.postForm<RagUploadResponse>("/v1/rag/upload", form);
  },
  chat: (payload: {
    thread_id: string;
    question: string;
    top_k?: number;
    document_ids?: string[];
  }) => api.post<RagChatResponse>("/v1/rag/chat", payload),
  listDocuments: (threadId: string) =>
    api.get<RagDocument[]>(`/v1/rag/documents?thread_id=${threadId}`),
  deleteDocument: (threadId: string, documentId: string) =>
    api.delete<{ deleted: boolean; document_id: string }>(
      `/v1/rag/documents/${documentId}?thread_id=${threadId}`
    ),
};
