import type {
  ResearchDigestDecision,
  ResearchDigestResponse,
  ResearchDigestSection,
  ResearchPaper,
} from "../types";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export interface StreamResearchDigestParams {
  topic: string;
  signal?: AbortSignal;
  onStatus?: (status: string) => void;
  onQuery?: (payload: { round: number; query: string }) => void;
  onPapers?: (payload: {
    round: number;
    query: string;
    new_count: number;
    papers: ResearchPaper[];
  }) => void;
  onDecision?: (
    payload: ResearchDigestDecision & { round: number; paper_count: number }
  ) => void;
  onSection?: (payload: ResearchDigestSection) => void;
  onDone?: (payload: ResearchDigestResponse) => void;
}

export async function streamResearchDigest({
  topic,
  signal,
  onStatus,
  onQuery,
  onPapers,
  onDecision,
  onSection,
  onDone,
}: StreamResearchDigestParams): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/research-digest/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ topic }),
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

      if (event.event === "status" && typeof event.data === "string") {
        onStatus?.(event.data);
      } else if (event.event === "query" && event.data) {
        onQuery?.(event.data as { round: number; query: string });
      } else if (event.event === "papers" && event.data) {
        onPapers?.(
          event.data as {
            round: number;
            query: string;
            new_count: number;
            papers: ResearchPaper[];
          }
        );
      } else if (event.event === "decision" && event.data) {
        onDecision?.(
          event.data as ResearchDigestDecision & {
            round: number;
            paper_count: number;
          }
        );
      } else if (event.event === "section" && event.data) {
        onSection?.(event.data as ResearchDigestSection);
      } else if (event.event === "error") {
        const message =
          typeof event.data === "string"
            ? event.data
            : typeof event.message === "string"
              ? event.message
              : "Research digest failed";
        throw new Error(message);
      } else if (event.event === "done" && event.data) {
        onDone?.(event.data as ResearchDigestResponse);
        return;
      }
    }
  }
}
