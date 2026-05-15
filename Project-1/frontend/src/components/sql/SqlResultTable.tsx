interface Props {
  rows: Record<string, unknown>[];
}

export function SqlResultTable({ rows }: Props) {
  if (rows.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
        No rows returned.
      </div>
    );
  }

  const columns = Object.keys(rows[0]);

  return (
    <div className="overflow-auto rounded-xl border border-slate-200 bg-white">
      <table className="min-w-full text-sm">
        <thead className="bg-slate-100">
          <tr>
            {columns.map((col) => (
              <th key={col} className="px-3 py-2 text-left font-semibold text-slate-700">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={idx} className="border-t border-slate-100">
              {columns.map((col) => (
                <td key={`${idx}-${col}`} className="px-3 py-2 text-slate-700">
                  {String(row[col] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
