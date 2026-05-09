import { useState } from "react";

import type { RagDocument, RagUploadResponse } from "../../types";
import { DocumentCard } from "./DocumentCard";
import { PDFUploader } from "./PDFUploader";

interface DocumentSidebarProps {
  threadId: string;
  documents: RagDocument[];
  loading: boolean;
  onUploaded: (payload: RagUploadResponse) => void;
  onDelete: (documentId: string) => Promise<void>;
}

export function DocumentSidebar({
  threadId,
  documents,
  loading,
  onUploaded,
  onDelete,
}: DocumentSidebarProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  return (
    <aside className="w-full rounded-2xl border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-950 lg:w-[340px]">
      <h2 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">
        Thread Documents
      </h2>

      <PDFUploader threadId={threadId} onUploaded={onUploaded} />

      <div className="mt-3 space-y-2">
        {loading ? (
          <p className="text-xs text-gray-500 dark:text-gray-400">Loading documents...</p>
        ) : documents.length === 0 ? (
          <p className="text-xs text-gray-500 dark:text-gray-400">No PDFs uploaded for this thread yet.</p>
        ) : (
          documents.map((doc) => (
            <DocumentCard
              key={doc.id}
              document={doc}
              deleting={deletingId === doc.id}
              onDelete={async () => {
                setDeletingId(doc.id);
                try {
                  await onDelete(doc.id);
                } finally {
                  setDeletingId(null);
                }
              }}
            />
          ))
        )}
      </div>
    </aside>
  );
}
