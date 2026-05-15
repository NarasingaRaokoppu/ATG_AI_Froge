import { useMemo, useState } from "react";

import { GoogleSheetConnect } from "../components/spreadsheet/GoogleSheetConnect";
import { SpreadsheetChart } from "../components/spreadsheet/SpreadsheetChart";
import { SpreadsheetQueryInput } from "../components/spreadsheet/SpreadsheetQueryInput";
import { SpreadsheetResultTable } from "../components/spreadsheet/SpreadsheetResultTable";
import { SpreadsheetUpload } from "../components/spreadsheet/SpreadsheetUpload";
import { useSpreadsheetChat } from "../hooks/useSpreadsheetChat";
import type { SpreadsheetAgentResponse, SpreadsheetSession } from "../types";

export default function SpreadsheetExplorerPage() {
  const [threadId, setThreadId] = useState<string | null>(null);
  const [activeSession, setActiveSession] = useState<SpreadsheetSession | null>(null);
  const [question, setQuestion] = useState("");
  const [generatedCode, setGeneratedCode] = useState("");
  const [liveAnswer, setLiveAnswer] = useState("");
  const [result, setResult] = useState<SpreadsheetAgentResponse | null>(null);
  const [errorText, setErrorText] = useState<string | null>(null);

  const {
    historyQuery,
    uploadMutation,
    connectGoogleSheetMutation,
    ensureThread,
    streamSpreadsheetQuery,
  } = useSpreadsheetChat(threadId);

  const rows = useMemo(() => result?.rows ?? [], [result]);
  const columns = useMemo(() => result?.columns ?? [], [result]);
  const chart = useMemo(
    () => result?.chart ?? { chart_type: "table" as const },
    [result]
  );

  const handleUpload = async (file: File) => {
    const resolvedThreadId = await ensureThread();
    setThreadId(resolvedThreadId);
    const response = await uploadMutation.mutateAsync({ threadId: resolvedThreadId, file });
    setActiveSession(response.session);
    setErrorText(null);
  };

  const handleConnectGoogleSheet = async (payload: {
    google_sheet_url?: string;
    spreadsheet_id?: string;
    worksheet_title?: string;
  }) => {
    const resolvedThreadId = await ensureThread();
    setThreadId(resolvedThreadId);
    const response = await connectGoogleSheetMutation.mutateAsync({
      thread_id: resolvedThreadId,
      ...payload,
    });
    setActiveSession(response.session);
    setErrorText(null);
  };

  const handleQuery = async () => {
    if (!activeSession || !question.trim()) return;
    const resolvedThreadId = threadId ?? (await ensureThread());
    setThreadId(resolvedThreadId);
    setGeneratedCode("");
    setLiveAnswer("");
    setResult(null);
    setErrorText(null);

    try {
      await streamSpreadsheetQuery({
        threadId: resolvedThreadId,
        spreadsheetSessionId: activeSession.id,
        question,
        onCode: setGeneratedCode,
        onToken: (token) => setLiveAnswer((prev) => prev + token),
        onDone: (payload) => setResult(payload),
      });
      await historyQuery.refetch();
    } catch (error) {
      setErrorText(error instanceof Error ? error.message : "Spreadsheet query failed");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-100 to-white p-4 md:p-6">
      <div className="mx-auto grid max-w-7xl gap-4 lg:grid-cols-[340px_1fr]">
        <aside className="space-y-4">
          <SpreadsheetUpload busy={uploadMutation.isPending} onSelect={handleUpload} />
          <GoogleSheetConnect
            busy={connectGoogleSheetMutation.isPending}
            onConnect={handleConnectGoogleSheet}
          />
          <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
            <div className="font-medium text-slate-900">Active source</div>
            <div className="mt-2">{activeSession ? activeSession.original_filename || activeSession.google_sheet_url || activeSession.id : "None selected"}</div>
            <div className="mt-2 text-xs text-slate-500">
              {threadId ? `Thread: ${threadId}` : "Thread will be created automatically."}
            </div>
          </div>
        </aside>

        <main className="space-y-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <h1 className="text-2xl font-semibold text-slate-900">Spreadsheet Explorer</h1>
            <p className="mt-1 text-sm text-slate-600">
              Upload CSV or Excel files, connect Google Sheets, and ask questions in natural language.
            </p>
          </div>

          <SpreadsheetQueryInput
            question={question}
            onChange={setQuestion}
            onSubmit={handleQuery}
            disabled={!activeSession}
          />

          {errorText && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {errorText}
            </div>
          )}

          <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Generated Pandas Code
              </div>
              <pre className="mt-1 overflow-auto rounded-lg bg-slate-950 p-3 text-xs text-emerald-300">
                {generatedCode || result?.generated_code || "-"}
              </pre>
            </div>
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Answer
              </div>
              <p className="mt-1 text-sm text-slate-700">{result?.answer || liveAnswer || "-"}</p>
            </div>
            {result && (
              <div className="text-xs text-slate-500">Execution: {result.execution_ms} ms</div>
            )}
          </div>

          <SpreadsheetChart rows={rows} chart={chart} />
          <SpreadsheetResultTable columns={columns} rows={rows} />

          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <h2 className="text-lg font-semibold text-slate-900">History</h2>
            <div className="mt-3 space-y-2">
              {(historyQuery.data ?? []).map((item) => (
                <div key={item.id} className="rounded-lg border border-slate-200 p-3">
                  <div className="text-xs text-slate-500">{new Date(item.created_at).toLocaleString()}</div>
                  <div className="text-sm font-medium text-slate-800">{item.question}</div>
                  <div className="mt-1 text-xs text-slate-600">{item.answer_summary}</div>
                </div>
              ))}
              {historyQuery.data?.length === 0 && (
                <div className="text-sm text-slate-500">No spreadsheet history yet for this thread.</div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
