/**
 * Streaming helpers for SSE chat responses.
 *
 * Each SSE frame's `data:` payload is JSON shaped as:
 *   {"event":"thread","thread_id":"..."}
 *   {"event":"token","data":"..."}
 *   {"event":"done"}
 *   {"event":"error","error":"...","message":"..."}
 */

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api";

import type { MessageAttachment } from "../types";

export interface StreamChatOptions {
  message: string;
  threadId: string | null;
  attachments?: MessageAttachment[];
  signal?: AbortSignal;
  onThread: (threadId: string) => void;
  onToken: (token: string) => void;
}

export async function streamChat({
  message,
  threadId,
  attachments = [],
  signal,
  onThread,
  onToken,
}: StreamChatOptions): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ message, thread_id: threadId, attachments }),
    credentials: "include",
    signal,
  });

  if (!response.ok || !response.body) {
    let detail: unknown = response.statusText;
    try {
      detail = (await response.json()).detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(
      typeof detail === "string" ? detail : JSON.stringify(detail)
    );
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    let sepIndex: number;
    while ((sepIndex = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, sepIndex);
      buffer = buffer.slice(sepIndex + 2);

      const dataLines: string[] = [];
      for (const rawLine of frame.split("\n")) {
        const line = rawLine.trimEnd();
        if (line.startsWith("data:")) {
          dataLines.push(line.slice(5).replace(/^ /, ""));
        }
      }
      if (dataLines.length === 0) continue;

      const payload = dataLines.join("\n");
      let event: { event: string; [k: string]: unknown };
      try {
        event = JSON.parse(payload);
      } catch {
        continue;
      }

      if (event.event === "thread" && typeof event.thread_id === "string") {
        onThread(event.thread_id);
      } else if (event.event === "token" && typeof event.data === "string") {
        onToken(event.data);
      } else if (event.event === "done") {
        return;
      } else if (event.event === "error") {
        throw new Error(
          (event.message as string) || (event.error as string) || "Stream error"
        );
      }
    }
  }
}
