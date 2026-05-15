interface Props {
  sql: string;
  explanation: string;
  executionTimeMs?: number;
}

export function SqlQueryInspector({ sql, explanation, executionTimeMs }: Props) {
  return (
    <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Generated SQL
        </h3>
        <pre className="mt-1 overflow-auto rounded-lg bg-slate-950 p-3 text-xs text-emerald-300">
          {sql || "-"}
        </pre>
      </div>
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Explanation
        </h3>
        <p className="mt-1 text-sm text-slate-700">{explanation || "-"}</p>
      </div>
      {typeof executionTimeMs === "number" && (
        <div className="text-xs text-slate-500">Execution: {executionTimeMs} ms</div>
      )}
    </div>
  );
}
