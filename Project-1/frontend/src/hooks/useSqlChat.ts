import { useMutation, useQuery } from "@tanstack/react-query";

import { api } from "../lib/api";
import type {
  SpreadsheetQueryResponse,
  SqlQueryHistoryItem,
  SqlQueryResponse,
} from "../types";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export interface StreamSqlParams {
  threadId: string;
  connectionId: string;
  question: string;
  signal?: AbortSignal;
  onSql?: (sql: string) => void;
  onToken?: (token: string) => void;
  onDone?: (payload: SqlQueryResponse) => void;
}

async function streamSqlQuery({
  threadId,
  connectionId,
  question,
  signal,
  onSql,
  onToken,
  onDone,
}: StreamSqlParams): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({
      thread_id: threadId,
      connection_id: connectionId,
      question,
    }),
    credentials: "include",
    signal,
  });

  if (!response.ok || !response.body) {
    let detail: unknown = response.statusText;
    try {
      detail = (await response.json()).detail ?? detail;
    } catch {
      /* noop */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
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

      const payloadLines: string[] = [];
      for (const line of frame.split("\n")) {
        const normalized = line.trimEnd();
        if (normalized.startsWith("data:")) {
          payloadLines.push(normalized.slice(5).trimStart());
        }
      }
      if (payloadLines.length === 0) continue;

      let event: { event: string; data?: unknown; message?: unknown };
      try {
        event = JSON.parse(payloadLines.join("\n"));
      } catch {
        continue;
      }

      if (event.event === "sql" && typeof event.data === "string") {
        onSql?.(event.data);
      } else if (event.event === "token" && typeof event.data === "string") {
        onToken?.(event.data);
      } else if (event.event === "error") {
        const message =
          typeof event.data === "string"
            ? event.data
            : typeof event.message === "string"
              ? event.message
              : "SQL stream failed";
        throw new Error(message);
      } else if (event.event === "done" && event.data) {
        onDone?.(event.data as SqlQueryResponse);
        return;
      }
    }
  }
}

export function useSqlChat(threadId: string | null) {
  const historyQuery = useQuery({
    queryKey: ["sql-history", threadId],
    queryFn: () => api.get<SqlQueryHistoryItem[]>(`/history/${threadId}`),
    enabled: Boolean(threadId),
  });

  const spreadsheetQuery = useMutation({
    mutationFn: (payload: {
      thread_id?: string;
      question: string;
      spreadsheet_session_id?: string;
      google_sheet_url?: string;
      file_path?: string;
    }) =>
      api.post<SpreadsheetQueryResponse>("/spreadsheet/query", {
        thread_id: payload.thread_id ?? threadId,
        question: payload.question,
        spreadsheet_session_id: payload.spreadsheet_session_id ?? null,
        google_sheet_url: payload.google_sheet_url ?? null,
        file_path: payload.file_path ?? null,
      }),
  });

  return {
    historyQuery,
    spreadsheetQuery,
    streamSqlQuery,
  };
}
