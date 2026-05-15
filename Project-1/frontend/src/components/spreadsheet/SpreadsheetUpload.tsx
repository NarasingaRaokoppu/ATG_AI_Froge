interface Props {
  busy?: boolean;
  onSelect: (file: File) => void | Promise<void>;
}

export function SpreadsheetUpload({ busy, onSelect }: Props) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-500">
        Upload CSV or Excel
      </label>
      <input
        type="file"
        accept=".csv,.xlsx,.xls"
        disabled={busy}
        className="block w-full rounded-lg border border-slate-300 p-2 text-sm"
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) {
            void onSelect(file);
          }
          event.currentTarget.value = "";
        }}
      />
    </div>
  );
}
