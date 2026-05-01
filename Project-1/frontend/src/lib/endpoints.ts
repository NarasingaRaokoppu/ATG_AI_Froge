/**
 * Auth + thread + message API helpers.
 * Built on top of the centralized fetch client in `./api`.
 */

import { api } from "./api";
import type {
  MessageDTO,
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
