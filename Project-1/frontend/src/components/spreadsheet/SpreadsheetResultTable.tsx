interface Props {
  columns: string[];
  rows: Record<string, unknown>[];
}

export function SpreadsheetResultTable({ columns, rows }: Props) {
  if (rows.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
        No rows returned.
      </div>
    );
  }

  const visibleColumns = columns.length > 0 ? columns : Object.keys(rows[0]);

  return (
    <div className="overflow-auto rounded-xl border border-slate-200 bg-white">
      <table className="min-w-full text-sm">
        <thead className="bg-slate-100">
          <tr>
            {visibleColumns.map((column) => (
              <th key={column} className="px-3 py-2 text-left font-semibold text-slate-700">
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index} className="border-t border-slate-100">
              {visibleColumns.map((column) => (
                <td key={`${index}-${column}`} className="px-3 py-2 text-slate-700">
                  {String(row[column] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
