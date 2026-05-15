import { useEffect, useMemo, useState } from "react";

import { ConnectionList } from "../components/sql/ConnectionList";
import { DatabaseConnectionModal } from "../components/sql/DatabaseConnectionModal";
import { SpreadsheetUpload } from "../components/sql/SpreadsheetUpload";
import { SqlChart } from "../components/sql/SqlChart";
import { SqlQueryInspector } from "../components/sql/SqlQueryInspector";
import { SqlResultTable } from "../components/sql/SqlResultTable";
import { useDatabaseConnections } from "../hooks/useDatabaseConnections";
import { useSqlChat } from "../hooks/useSqlChat";
import { threadApi } from "../lib/endpoints";
import type {
  DatabaseConnection,
  DatabaseConnectionCreateInput,
  DatabaseConnectionUpdateInput,
  SpreadsheetQueryResponse,
  SqlQueryResponse,
} from "../types";

export default function DataExplorerPage() {
  const {
    data: connections = [],
    isLoading,
    createConnection,
    updateConnection,
    deleteConnection,
    testConnection,
  } = useDatabaseConnections();

  const [activeConnectionId, setActiveConnectionId] = useState<string | null>(null);
  const [threadId, setThreadId] = useState("");
  const [question, setQuestion] = useState("");
  const [googleSheetUrl, setGoogleSheetUrl] = useState("");
  const [uploadedPath, setUploadedPath] = useState("");
  const [liveSql, setLiveSql] = useState("");
  const [liveExplanation, setLiveExplanation] = useState("");
  const [queryResult, setQueryResult] = useState<SqlQueryResponse | null>(null);
  const [spreadsheetResult, setSpreadsheetResult] =
    useState<SpreadsheetQueryResponse | null>(null);
  const [errorText, setErrorText] = useState<string | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<DatabaseConnection | null>(null);

  const { streamSqlQuery, spreadsheetQuery, historyQuery } = useSqlChat(
    threadId || null
  );

  useEffect(() => {
    if (!activeConnectionId && connections.length > 0) {
      setActiveConnectionId(connections[0].id);
    }
  }, [activeConnectionId, connections]);

  const selectedRows = useMemo(
    () => queryResult?.rows ?? spreadsheetResult?.rows ?? [],
    [queryResult, spreadsheetResult]
  );

  const selectedChart = useMemo(
    () =>
      queryResult?.chart_suggestion ??
      spreadsheetResult?.chart_suggestion ?? {
        chart_type: "table" as const,
      },
    [queryResult, spreadsheetResult]
  );

  const handleConnectionSubmit = async (
    payload: DatabaseConnectionCreateInput | DatabaseConnectionUpdateInput
  ) => {
    if (editing) {
      await updateConnection.mutateAsync({ id: editing.id, payload });
    } else {
      await createConnection.mutateAsync(payload as DatabaseConnectionCreateInput);
    }
  };

  const ensureThreadId = async (): Promise<string> => {
    if (threadId.trim()) {
      return threadId.trim();
    }

    const created = await threadApi.create("Data Explorer");
    setThreadId(created.id);
    return created.id;
  };

  const runDatabaseQuery = async () => {
    if (!activeConnectionId || !question.trim()) return;
    setLiveExplanation("");
    setLiveSql("");
    setQueryResult(null);
    setSpreadsheetResult(null);
    setErrorText(null);

    try {
      const resolvedThreadId = await ensureThreadId();
      await streamSqlQuery({
        threadId: resolvedThreadId,
        connectionId: activeConnectionId,
        question,
        onSql: setLiveSql,
        onToken: (token) => setLiveExplanation((prev) => prev + token),
        onDone: (payload) => setQueryResult(payload),
      });
    } catch (err) {
      setErrorText(err instanceof Error ? err.message : "Query failed");
    }
  };

  const runSpreadsheetQuery = async () => {
    if (!question.trim()) return;
    setQueryResult(null);
    setSpreadsheetResult(null);
    setErrorText(null);

    try {
      const resolvedThreadId = await ensureThreadId();
      const result = await spreadsheetQuery.mutateAsync({
        thread_id: resolvedThreadId,
        question,
        google_sheet_url: googleSheetUrl || undefined,
        file_path: uploadedPath || undefined,
      });
      setSpreadsheetResult(result);
    } catch (err) {
      setErrorText(err instanceof Error ? err.message : "Spreadsheet query failed");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-100 to-white p-4 md:p-6">
      <div className="mx-auto grid max-w-7xl gap-4 lg:grid-cols-[340px_1fr]">
        <aside className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Data Sources</h2>
            <button
              className="rounded-lg bg-slate-900 px-3 py-1.5 text-sm text-white"
              onClick={() => {
                setEditing(null);
                setModalOpen(true);
              }}
            >
              Add
            </button>
          </div>

          {isLoading ? (
            <div className="text-sm text-slate-500">Loading connections...</div>
          ) : (
            <ConnectionList
              connections={connections}
              activeConnectionId={activeConnectionId}
              onSelect={setActiveConnectionId}
              onEdit={(item) => {
                setEditing(item);
                setModalOpen(true);
              }}
              onDelete={async (item) => {
                await deleteConnection.mutateAsync(item.id);
                if (activeConnectionId === item.id) {
                  setActiveConnectionId(null);
                }
              }}
              onTest={async (item) => {
                const result = await testConnection.mutateAsync(item.id);
                alert(result.message);
              }}
            />
          )}

          <SpreadsheetUpload onUploadedPath={setUploadedPath} />

          <div className="rounded-xl border border-slate-200 bg-white p-3">
            <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-500">
              Google Sheet URL
            </label>
            <input
              className="w-full rounded-lg border border-slate-300 p-2 text-sm"
              placeholder="https://docs.google.com/spreadsheets/..."
              value={googleSheetUrl}
              onChange={(e) => setGoogleSheetUrl(e.target.value)}
            />
          </div>
        </aside>

        <main className="space-y-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <h1 className="text-2xl font-semibold text-slate-900">Data Explorer</h1>
            <p className="mt-1 text-sm text-slate-600">
              Ask natural-language questions over SQL databases and spreadsheets.
            </p>

            <div className="mt-4 grid gap-3 md:grid-cols-4">
              <input
                className="rounded-lg border border-slate-300 p-2 text-sm md:col-span-1"
                placeholder="Thread ID (auto-created if left blank)"
                value={threadId}
                onChange={(e) => setThreadId(e.target.value)}
              />
              <input
                className="rounded-lg border border-slate-300 p-2 text-sm md:col-span-2"
                placeholder="e.g. Show top 10 customers by revenue this month"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
              />
              <div className="flex gap-2">
                <button
                  className="flex-1 rounded-lg bg-slate-900 px-3 py-2 text-sm text-white disabled:opacity-50"
                  disabled={!activeConnectionId || !question.trim()}
                  onClick={() => void runDatabaseQuery()}
                >
                  Query DB
                </button>
                <button
                  className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 disabled:opacity-50"
                  disabled={
                    !question.trim() ||
                    (!uploadedPath.trim() && !googleSheetUrl.trim())
                  }
                  onClick={() => void runSpreadsheetQuery()}
                >
                  Query Sheet
                </button>
              </div>
            </div>
            <div className="mt-2 text-xs text-slate-500">
              {threadId.trim()
                ? `Using thread: ${threadId}`
                : "A thread will be created automatically when you run your first query."}
            </div>
            {errorText && (
              <div className="mt-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
                {errorText}
              </div>
            )}
          </div>

          <SqlQueryInspector
            sql={queryResult?.generated_sql || liveSql || spreadsheetResult?.generated_code || ""}
            explanation={queryResult?.explanation || spreadsheetResult?.explanation || liveExplanation}
            executionTimeMs={queryResult?.execution_time_ms}
          />

          <SqlChart rows={selectedRows} chart={selectedChart} />
          <SqlResultTable rows={selectedRows} />

          <div className="rounded-2xl border border-slate-200 bg-white p-4">
            <h2 className="text-lg font-semibold text-slate-900">History</h2>
            <div className="mt-3 space-y-2">
              {(historyQuery.data ?? []).map((item) => (
                <div key={item.id} className="rounded-lg border border-slate-200 p-3">
                  <div className="text-xs text-slate-500">{new Date(item.created_at).toLocaleString()}</div>
                  <div className="text-sm font-medium text-slate-800">{item.user_question}</div>
                  <div className="mt-1 text-xs text-slate-600">{item.assistant_summary}</div>
                </div>
              ))}
              {historyQuery.data?.length === 0 && (
                <div className="text-sm text-slate-500">No SQL history yet for this thread.</div>
              )}
            </div>
          </div>
        </main>
      </div>

      <DatabaseConnectionModal
        open={modalOpen}
        editing={editing}
        onClose={() => {
          setModalOpen(false);
          setEditing(null);
        }}
        onSubmit={handleConnectionSubmit}
      />
    </div>
  );
}
