import { useState } from "react";

interface Props {
  busy?: boolean;
  onConnect: (payload: {
    google_sheet_url?: string;
    spreadsheet_id?: string;
    worksheet_title?: string;
  }) => void | Promise<void>;
}

export function GoogleSheetConnect({ busy, onConnect }: Props) {
  const [googleSheetUrl, setGoogleSheetUrl] = useState("");
  const [spreadsheetId, setSpreadsheetId] = useState("");
  const [worksheetTitle, setWorksheetTitle] = useState("");

  return (
    <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        Google Sheets
      </div>
      <input
        className="w-full rounded-lg border border-slate-300 p-2 text-sm"
        placeholder="Google Sheet URL"
        value={googleSheetUrl}
        onChange={(event) => setGoogleSheetUrl(event.target.value)}
      />
      <input
        className="w-full rounded-lg border border-slate-300 p-2 text-sm"
        placeholder="Spreadsheet ID"
        value={spreadsheetId}
        onChange={(event) => setSpreadsheetId(event.target.value)}
      />
      <input
        className="w-full rounded-lg border border-slate-300 p-2 text-sm"
        placeholder="Worksheet title (optional)"
        value={worksheetTitle}
        onChange={(event) => setWorksheetTitle(event.target.value)}
      />
      <button
        className="rounded-lg bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50"
        disabled={busy || (!googleSheetUrl.trim() && !spreadsheetId.trim())}
        onClick={() =>
          void onConnect({
            google_sheet_url: googleSheetUrl || undefined,
            spreadsheet_id: spreadsheetId || undefined,
            worksheet_title: worksheetTitle || undefined,
          })
        }
      >
        Connect Sheet
      </button>
    </div>
  );
}
