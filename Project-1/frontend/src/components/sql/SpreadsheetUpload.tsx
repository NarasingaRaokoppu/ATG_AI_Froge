import { useRef } from "react";

import { uploadService } from "../../services/uploadService";

interface Props {
  onUploadedPath: (path: string) => void;
}

export function SpreadsheetUpload({ onUploadedPath }: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const uploaded = await uploadService.uploadFiles([file]);
    const first = uploaded[0];
    if (first?.attachment_url) {
      onUploadedPath(first.attachment_url);
    }

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3">
      <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-500">
        Spreadsheet source
      </label>
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.xlsx,.xls,.xlsm,.xlsb"
        onChange={handleChange}
        className="block w-full rounded-lg border border-slate-300 p-2 text-sm"
      />
      <p className="mt-2 text-xs text-slate-500">Upload CSV or Excel to query with natural language.</p>
    </div>
  );
}
