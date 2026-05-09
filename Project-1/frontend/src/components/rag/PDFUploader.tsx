import { useRef, useState } from "react";

import type { RagUploadResponse } from "../../types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
const MAX_MB = 50;

interface PDFUploaderProps {
  threadId: string;
  onUploaded: (payload: RagUploadResponse) => void;
}

export function PDFUploader({ threadId, onUploaded }: PDFUploaderProps) {
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const uploadFile = async (file: File) => {
    if (file.type !== "application/pdf") {
      setError("Only PDF files are allowed.");
      return;
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      setError(`File is too large. Max size is ${MAX_MB}MB.`);
      return;
    }

    setUploading(true);
    setProgress(0);
    setError(null);

    const form = new FormData();
    form.append("thread_id", threadId);
    form.append("file", file);

    try {
      const response = await new Promise<RagUploadResponse>((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open("POST", `${API_BASE_URL}/v1/rag/upload`, true);
        xhr.withCredentials = true;

        xhr.upload.onprogress = (event) => {
          if (!event.lengthComputable) return;
          setProgress(Math.round((event.loaded / event.total) * 100));
        };

        xhr.onload = () => {
          try {
            if (xhr.status < 200 || xhr.status >= 300) {
              reject(new Error(xhr.responseText || `Upload failed (${xhr.status})`));
              return;
            }
            resolve(JSON.parse(xhr.responseText) as RagUploadResponse);
          } catch (parseError) {
            reject(parseError);
          }
        };

        xhr.onerror = () => reject(new Error("Network error during upload"));
        xhr.send(form);
      });

      onUploaded(response);
      setProgress(100);
      if (inputRef.current) inputRef.current.value = "";
    } catch (err) {
      const message = err instanceof Error ? err.message : "Upload failed";
      setError(message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-900">
      <div className="flex items-center justify-between gap-2">
        <label className="cursor-pointer rounded-lg bg-blue-600 px-3 py-2 text-xs font-semibold text-white hover:bg-blue-700">
          Upload PDF
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf,.pdf"
            disabled={uploading}
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void uploadFile(file);
            }}
          />
        </label>
        {uploading && <span className="text-xs text-gray-600 dark:text-gray-300">{progress}%</span>}
      </div>
      {uploading && (
        <div className="mt-2 h-2 overflow-hidden rounded bg-gray-200 dark:bg-gray-700">
          <div
            className="h-full bg-blue-600 transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
      {error && <p className="mt-2 text-xs text-rose-600 dark:text-rose-400">{error}</p>}
    </div>
  );
}
