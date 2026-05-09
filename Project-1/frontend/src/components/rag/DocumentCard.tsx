import type { RagDocument } from "../../types";

interface DocumentCardProps {
  document: RagDocument;
  deleting: boolean;
  onDelete: () => void;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
}

export function DocumentCard({ document, deleting, onDelete }: DocumentCardProps) {
  const statusColor: Record<RagDocument["status"], string> = {
    queued: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200",
    processing:
      "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200",
    processed:
      "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-200",
    failed: "bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-200",
  };

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-3 shadow-sm dark:border-gray-700 dark:bg-gray-900">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="line-clamp-1 text-sm font-semibold text-gray-900 dark:text-gray-100">
            {document.filename}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {formatBytes(document.file_size)} · {document.chunk_count} chunks
          </p>
        </div>
        <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${statusColor[document.status]}`}>
          {document.status}
        </span>
      </div>

      <div className="mt-2 flex justify-end">
        <button
          type="button"
          onClick={onDelete}
          disabled={deleting}
          className="rounded-md border border-rose-200 px-2 py-1 text-xs text-rose-700 hover:bg-rose-50 disabled:opacity-60 dark:border-rose-800 dark:text-rose-300 dark:hover:bg-rose-950/40"
        >
          {deleting ? "Deleting..." : "Delete"}
        </button>
      </div>
    </div>
  );
}
