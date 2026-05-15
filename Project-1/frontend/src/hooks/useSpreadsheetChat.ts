import { useMutation, useQuery } from "@tanstack/react-query";

import { spreadsheetApi, threadApi } from "../lib/endpoints";
import type { SpreadsheetAgentResponse } from "../types";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api";

interface StreamSpreadsheetParams {
  threadId: string;
  spreadsheetSessionId: string;
  question: string;
  signal?: AbortSignal;
  onCode?: (code: string) => void;
  onToken?: (token: string) => void;
  onDone?: (payload: SpreadsheetAgentResponse) => void;
}

async function streamSpreadsheetQuery({
  threadId,
  spreadsheetSessionId,
  question,
  signal,
  onCode,
  onToken,
  onDone,
}: StreamSpreadsheetParams): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/spreadsheet/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({
      thread_id: threadId,
      spreadsheet_session_id: spreadsheetSessionId,
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

      if (event.event === "code" && typeof event.data === "string") {
        onCode?.(event.data);
      } else if (event.event === "token" && typeof event.data === "string") {
        onToken?.(event.data);
      } else if (event.event === "error") {
        throw new Error(
          typeof event.message === "string" ? event.message : "Spreadsheet query failed"
        );
      } else if (event.event === "done" && event.data) {
        onDone?.(event.data as SpreadsheetAgentResponse);
        return;
      }
    }
  }
}

export function useSpreadsheetChat(threadId: string | null) {
  const historyQuery = useQuery({
    queryKey: ["spreadsheet-history", threadId],
    queryFn: () => spreadsheetApi.history(threadId!),
    enabled: Boolean(threadId),
  });

  const uploadMutation = useMutation({
    mutationFn: async ({ threadId, file }: { threadId: string; file: File }) => {
      return spreadsheetApi.upload(threadId, file);
    },
  });

  const connectGoogleSheetMutation = useMutation({
    mutationFn: (payload: {
      thread_id: string;
      google_sheet_url?: string;
      spreadsheet_id?: string;
      worksheet_title?: string;
    }) => spreadsheetApi.connectGoogleSheet(payload),
  });

  const ensureThread = async (): Promise<string> => {
    if (threadId) return threadId;
    const created = await threadApi.create("Spreadsheet Explorer");
    return created.id;
  };

  return {
    historyQuery,
    uploadMutation,
    connectGoogleSheetMutation,
    ensureThread,
    streamSpreadsheetQuery,
  };
}
