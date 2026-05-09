import type { RagCitation } from "../../types";

interface SourceCitationProps {
  citation: RagCitation;
}

export function SourceCitation({ citation }: SourceCitationProps) {
  return (
    <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-2 text-xs text-emerald-900 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-100">
      <p className="font-semibold">{citation.filename}</p>
      <p>
        Page {citation.page_number ?? "n/a"} · Score {(citation.score * 100).toFixed(1)}%
      </p>
      <p className="mt-1 line-clamp-3 text-emerald-800 dark:text-emerald-200">
        {citation.content_preview}
      </p>
    </div>
  );
}
