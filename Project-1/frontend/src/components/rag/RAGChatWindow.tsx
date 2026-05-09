import { useState, type FormEvent } from "react";

import { ragApi } from "../../lib/endpoints";
import type { RagChatResponse, RagDocument } from "../../types";
import { SourceCitation } from "./SourceCitation";

interface RAGChatWindowProps {
  threadId: string;
  documents: RagDocument[];
}

interface RagTurn {
  id: string;
  question: string;
  response: RagChatResponse;
}

const newId = () =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2);

export function RAGChatWindow({ threadId, documents }: RAGChatWindowProps) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [turns, setTurns] = useState<RagTurn[]>([]);

  const processedDocs = documents.filter((d) => d.status === "processed");

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const q = question.trim();
    if (!q || loading || processedDocs.length === 0) return;

    setLoading(true);
    setError(null);
    try {
      const response = await ragApi.chat({
        thread_id: threadId,
        question: q,
        document_ids: processedDocs.map((d) => d.id),
      });
      setTurns((prev) => [{ id: newId(), question: q, response }, ...prev]);
      setQuestion("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "RAG chat failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="flex min-h-[380px] flex-1 flex-col rounded-2xl border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-950">
      <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">PDF RAG Chat</h2>
      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
        Ask thread-specific questions grounded in uploaded PDFs.
      </p>

      <form onSubmit={onSubmit} className="mt-3 flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={loading || processedDocs.length === 0}
          placeholder={
            processedDocs.length === 0
              ? "Upload and process a PDF first"
              : "Ask about your documents..."
          }
          className="flex-1 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
        />
        <button
          type="submit"
          disabled={loading || !question.trim() || processedDocs.length === 0}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-500"
        >
          {loading ? "Thinking..." : "Ask"}
        </button>
      </form>

      {error && <p className="mt-2 text-xs text-rose-600 dark:text-rose-400">{error}</p>}

      <div className="mt-3 flex-1 space-y-3 overflow-auto">
        {turns.length === 0 ? (
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Responses will include citations and page references.
          </p>
        ) : (
          turns.map((turn) => (
            <article
              key={turn.id}
              className="rounded-xl border border-gray-200 p-3 dark:border-gray-700"
            >
              <p className="text-xs font-semibold text-gray-500 dark:text-gray-400">Question</p>
              <p className="mt-1 text-sm text-gray-900 dark:text-gray-100">{turn.question}</p>

              <p className="mt-3 text-xs font-semibold text-gray-500 dark:text-gray-400">Answer</p>
              <p className="mt-1 text-sm text-gray-900 dark:text-gray-100">{turn.response.answer}</p>

              <div className="mt-2 flex items-center gap-2 text-xs">
                <span
                  className={`rounded-full px-2 py-0.5 font-semibold ${
                    turn.response.grounded
                      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
                      : "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300"
                  }`}
                >
                  {turn.response.grounded ? "Grounded" : "Low confidence"}
                </span>
                <span className="text-gray-500 dark:text-gray-400">
                  Confidence: {((turn.response.confidence ?? 0) * 100).toFixed(1)}%
                </span>
              </div>

              {turn.response.citations.length > 0 && (
                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  {turn.response.citations.map((citation) => (
                    <SourceCitation key={citation.chunk_id} citation={citation} />
                  ))}
                </div>
              )}
            </article>
          ))
        )}
      </div>
    </section>
  );
}
