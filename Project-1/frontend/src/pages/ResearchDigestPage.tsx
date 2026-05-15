import { useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Link } from "react-router-dom";

import { ProjectLinks } from "../components/navigation/ProjectLinks";
import { streamResearchDigest } from "../hooks/useResearchDigest";
import type {
  ResearchDigestDecision,
  ResearchDigestResponse,
  ResearchDigestSection,
  ResearchPaper,
} from "../types";

function mergePapers(current: ResearchPaper[], incoming: ResearchPaper[]) {
  const seen = new Set(current.map((paper) => paper.arxiv_id));
  const merged = [...current];
  for (const paper of incoming) {
    if (seen.has(paper.arxiv_id)) continue;
    seen.add(paper.arxiv_id);
    merged.push(paper);
  }
  return merged.sort((left, right) =>
    right.published.localeCompare(left.published)
  );
}

export default function ResearchDigestPage() {
  const [topic, setTopic] = useState("agentic retrieval augmented generation for enterprise knowledge systems");
  const [statusLog, setStatusLog] = useState<string[]>([]);
  const [queries, setQueries] = useState<Array<{ round: number; query: string }>>([]);
  const [papers, setPapers] = useState<ResearchPaper[]>([]);
  const [decision, setDecision] = useState<
    (ResearchDigestDecision & { round: number; paper_count: number }) | null
  >(null);
  const [sections, setSections] = useState<ResearchDigestSection[]>([]);
  const [result, setResult] = useState<ResearchDigestResponse | null>(null);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const completionState = useMemo(() => {
    if (isStreaming) return "Streaming digest...";
    if (result) return `Completed after ${result.rounds_completed} search rounds.`;
    return "Ready to search arXiv and build a live digest.";
  }, [isStreaming, result]);

  const handleRun = async () => {
    if (!topic.trim() || isStreaming) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setStatusLog([]);
    setQueries([]);
    setPapers([]);
    setDecision(null);
    setSections([]);
    setResult(null);
    setErrorText(null);
    setIsStreaming(true);

    try {
      await streamResearchDigest({
        topic: topic.trim(),
        signal: controller.signal,
        onStatus: (status) => setStatusLog((current) => [...current, status]),
        onQuery: (payload) => setQueries((current) => [...current, payload]),
        onPapers: (payload) => setPapers((current) => mergePapers(current, payload.papers)),
        onDecision: setDecision,
        onSection: (section) =>
          setSections((current) => {
            const next = current.filter((item) => item.id !== section.id);
            next.push(section);
            return next;
          }),
        onDone: setResult,
      });
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        setStatusLog((current) => [...current, "Digest run cancelled."]);
      } else {
        setErrorText(error instanceof Error ? error.message : "Research digest failed");
      }
    } finally {
      setIsStreaming(false);
    }
  };

  const handleCancel = () => {
    abortRef.current?.abort();
    setIsStreaming(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-100 to-white p-4 md:p-6">
      <div className="mx-auto max-w-7xl space-y-4">
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-3xl">
              <div className="text-xs font-semibold uppercase tracking-[0.22em] text-amber-600">
                Project 10
              </div>
              <h1 className="mt-2 text-3xl font-semibold text-slate-900">
                Research Digest Agent
              </h1>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Search arXiv iteratively, judge when the evidence is sufficient, and stream a structured digest section by section.
              </p>
            </div>
            <Link
              to="/chat"
              className="inline-flex rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
            >
              Back to Chat
            </Link>
          </div>
          <div className="mt-4">
            <ProjectLinks variant="compact" />
          </div>
        </div>

        <div className="grid gap-4 xl:grid-cols-[360px_1fr]">
          <aside className="space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="text-sm font-semibold text-slate-900">Research Brief</div>
              <div className="mt-3 space-y-3">
                <div>
                  <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Topic
                  </label>
                  <textarea
                    className="min-h-28 w-full rounded-xl border border-slate-300 p-3 text-sm text-slate-800 outline-none transition focus:border-slate-500"
                    value={topic}
                    onChange={(event) => setTopic(event.target.value)}
                    placeholder="Example: multimodal retrieval for enterprise support copilots"
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => void handleRun()}
                    disabled={isStreaming || !topic.trim()}
                    className="flex-1 rounded-xl bg-slate-900 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {isStreaming ? "Running..." : "Run Digest"}
                  </button>
                  <button
                    type="button"
                    onClick={handleCancel}
                    disabled={!isStreaming}
                    className="rounded-xl border border-slate-300 px-4 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="text-sm font-semibold text-slate-900">Agent State</div>
              <p className="mt-2 text-sm text-slate-600">{completionState}</p>
              {decision && (
                <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
                  <div className="font-medium">
                    Evidence {decision.enough_evidence ? "sufficient" : "still narrow"}
                  </div>
                  <div className="mt-1 text-xs text-amber-800">
                    Confidence: {Math.round(decision.confidence * 100)}% | Papers: {decision.paper_count} | Round: {decision.round}
                  </div>
                  <p className="mt-2 text-xs leading-5 text-amber-900">{decision.rationale}</p>
                  {decision.missing_angles.length > 0 && (
                    <div className="mt-2 text-xs text-amber-800">
                      Missing: {decision.missing_angles.join(", ")}
                    </div>
                  )}
                </div>
              )}
              {errorText && (
                <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
                  {errorText}
                </div>
              )}
            </div>
          </aside>

          <main className="space-y-4">
            <div className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
              <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-slate-900">Search Activity</h2>
                  <div className="text-xs text-slate-500">{queries.length} queries</div>
                </div>
                <div className="mt-4 space-y-3">
                  {statusLog.length === 0 && (
                    <div className="rounded-xl border border-dashed border-slate-300 p-4 text-sm text-slate-500">
                      Start a run to watch search planning, evidence checks, and digest generation in real time.
                    </div>
                  )}
                  {statusLog.map((item, index) => (
                    <div key={`${item}-${index}`} className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
                      {item}
                    </div>
                  ))}
                  {queries.map((item) => (
                    <div key={`${item.round}-${item.query}`} className="rounded-xl border border-slate-200 p-3">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">
                        Round {item.round}
                      </div>
                      <div className="mt-1 font-mono text-xs leading-5 text-slate-700">
                        {item.query}
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-slate-900">Evidence Stack</h2>
                  <div className="text-xs text-slate-500">{papers.length} papers</div>
                </div>
                <div className="mt-4 space-y-3">
                  {papers.length === 0 && (
                    <div className="rounded-xl border border-dashed border-slate-300 p-4 text-sm text-slate-500">
                      No papers collected yet.
                    </div>
                  )}
                  {papers.map((paper) => (
                    <article key={paper.arxiv_id} className="rounded-xl border border-slate-200 p-3">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="text-sm font-semibold text-slate-900">{paper.title}</div>
                          <div className="mt-1 text-xs text-slate-500">
                            {paper.arxiv_id} | {new Date(paper.published).getFullYear()} | {paper.primary_category || "uncategorized"}
                          </div>
                        </div>
                        <div className="flex gap-2 text-xs">
                          <a
                            href={paper.abs_url}
                            target="_blank"
                            rel="noreferrer"
                            className="rounded-full border border-slate-300 px-2 py-1 text-slate-600 hover:bg-slate-50"
                          >
                            Abstract
                          </a>
                          {paper.pdf_url && (
                            <a
                              href={paper.pdf_url}
                              target="_blank"
                              rel="noreferrer"
                              className="rounded-full border border-slate-300 px-2 py-1 text-slate-600 hover:bg-slate-50"
                            >
                              PDF
                            </a>
                          )}
                        </div>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-slate-600">{paper.summary}</p>
                    </article>
                  ))}
                </div>
              </section>
            </div>

            <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-slate-900">Structured Digest</h2>
                  <p className="mt-1 text-sm text-slate-600">
                    Sections appear as the backend completes them.
                  </p>
                </div>
                {result && (
                  <div className="text-xs text-slate-500">
                    Finalized with {result.papers.length} papers across {result.rounds_completed} rounds.
                  </div>
                )}
              </div>

              <div className="mt-4 space-y-4">
                {sections.length === 0 && (
                  <div className="rounded-xl border border-dashed border-slate-300 p-5 text-sm text-slate-500">
                    No digest sections streamed yet.
                  </div>
                )}
                {sections.map((section) => (
                  <article key={section.id} className="rounded-2xl border border-slate-200 p-4">
                    <h3 className="text-base font-semibold text-slate-900">{section.title}</h3>
                    <div className="prose prose-sm mt-3 max-w-none text-slate-700">
                      <ReactMarkdown>{section.content}</ReactMarkdown>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          </main>
        </div>
      </div>
    </div>
  );
}
