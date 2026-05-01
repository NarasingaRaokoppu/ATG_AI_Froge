import {
  useRef,
  useState,
  useEffect,
  type FormEvent,
  type KeyboardEvent,
} from "react";

import { uploadApi } from "../../lib/endpoints";
import type { MessageAttachment } from "../../types";

const MAX_MB = 20;
const MAX_BYTES = MAX_MB * 1024 * 1024;

type DraftKind = "code" | "table" | "formula";

const ATTACHMENT_EMOJI: Record<string, string> = {
  image: "🖼️",
  video: "🎥",
  code: "💻",
  table: "📊",
  formula: "∫",
};

interface InputBarProps {
  disabled: boolean;
  onSend: (payload: { message: string; attachments: MessageAttachment[] }) => void;
}

export function InputBar({ disabled, onSend }: InputBarProps) {
  const [value, setValue] = useState("");
  const [attachments, setAttachments] = useState<MessageAttachment[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Inline draft panel (code / table / formula)
  const [draftKind, setDraftKind] = useState<DraftKind | null>(null);
  const [draftContent, setDraftContent] = useState("");

  // + button popover
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-focus on mount
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  // Close popover on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    const trimmed = value.trim();
    if ((!trimmed && attachments.length === 0) || disabled || uploading) return;
    onSend({ message: trimmed || "Please analyze the attachments.", attachments });
    setValue("");
    setAttachments([]);
    setDraftKind(null);
    setDraftContent("");
    setUploadError(null);
    textareaRef.current?.focus();
  };

  const commitDraft = () => {
    const content = draftContent.trim();
    if (!content || !draftKind) return;
    setAttachments((prev) => [
      ...prev,
      { attachment_type: draftKind, content, name: `${draftKind}-snippet` },
    ]);
    setDraftContent("");
    setDraftKind(null);
  };

  const handleFileSelect = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploadError(null);

    for (const file of Array.from(files)) {
      if (file.size > MAX_BYTES) {
        setUploadError(`"${file.name}" exceeds the ${MAX_MB}MB file size limit.`);
        // Reset the file input so the same file can be re-selected after the error is dismissed
        if (fileInputRef.current) fileInputRef.current.value = "";
        return;
      }
    }

    setUploading(true);
    try {
      const uploaded: MessageAttachment[] = [];
      for (const file of Array.from(files)) {
        const result = await uploadApi.uploadFile(file);
        uploaded.push({
          attachment_type: result.attachment_type,
          attachment_url: result.attachment_url,
          name: result.name,
          mime_type: result.mime_type,
          metadata: { size_bytes: result.size_bytes },
        });
      }
      setAttachments((prev) => [...prev, ...uploaded]);
    } catch {
      setUploadError("Upload failed. Please try again.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const removeAttachment = (index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const openDraft = (kind: DraftKind) => {
    setDraftKind(kind);
    setMenuOpen(false);
  };

  const canSend =
    !disabled && !uploading && (value.trim().length > 0 || attachments.length > 0);

  return (
    <div className="border-t border-gray-200 bg-white px-3 py-3 dark:border-gray-800 dark:bg-gray-900 sm:px-4 sm:py-4">
      <div className="mx-auto w-full max-w-4xl space-y-2">

        {/* Attachment chips */}
        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {attachments.map((a, idx) => (
              <span
                key={`${a.attachment_type}-${idx}`}
                className="inline-flex items-center gap-1 rounded-full border border-gray-200 bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-700 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200"
              >
                <span>{ATTACHMENT_EMOJI[a.attachment_type] ?? "📎"}</span>
                <span className="max-w-[120px] truncate">{a.name || a.attachment_type}</span>
                <button
                  type="button"
                  onClick={() => removeAttachment(idx)}
                  className="ml-0.5 rounded-full p-0.5 text-gray-400 hover:bg-gray-200 hover:text-gray-700 dark:hover:bg-gray-700 dark:hover:text-gray-100"
                  aria-label={`Remove ${a.name || a.attachment_type}`}
                >
                  ✕
                </button>
              </span>
            ))}
          </div>
        )}

        {/* Inline draft panel */}
        {draftKind && (
          <div className="rounded-xl border border-blue-200 bg-blue-50 p-2 dark:border-blue-900 dark:bg-blue-950/30">
            <div className="mb-1 flex items-center justify-between">
              <span className="text-xs font-semibold text-blue-700 dark:text-blue-300">
                {ATTACHMENT_EMOJI[draftKind]} Add {draftKind}
              </span>
              <button
                type="button"
                onClick={() => { setDraftKind(null); setDraftContent(""); }}
                className="text-xs text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
              >
                ✕
              </button>
            </div>
            <textarea
              autoFocus
              value={draftContent}
              onChange={(e) => setDraftContent(e.target.value)}
              rows={4}
              placeholder={
                draftKind === "code"
                  ? "Paste your code here..."
                  : draftKind === "table"
                  ? 'Paste JSON array: [{"col": "val"}, ...]'
                  : "Enter formula or expression..."
              }
              className="w-full resize-y rounded-lg border border-gray-300 bg-white px-3 py-2 font-mono text-xs focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
            />
            <div className="mt-1.5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => { setDraftKind(null); setDraftContent(""); }}
                className="rounded-lg px-3 py-1 text-xs text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={commitDraft}
                disabled={!draftContent.trim()}
                className="rounded-lg bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-500"
              >
                Add
              </button>
            </div>
          </div>
        )}

        {/* Upload error */}
        {uploadError && (
          <p className="text-xs font-medium text-red-600 dark:text-red-400">
            {uploadError}
          </p>
        )}

        {/* Main input row */}
        <form onSubmit={submit} className="flex items-end gap-2">
          {/* + button with popover */}
          <div className="relative" ref={menuRef}>
            <button
              type="button"
              onClick={() => setMenuOpen((o) => !o)}
              disabled={disabled || uploading}
              className="flex h-10 w-10 items-center justify-center rounded-xl border border-gray-300 bg-white text-gray-600 transition hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
              aria-label="Add attachment"
            >
              <span className="text-lg font-light leading-none">+</span>
            </button>

            {menuOpen && (
              <div className="absolute bottom-12 left-0 z-20 min-w-[170px] rounded-xl border border-gray-200 bg-white py-1 shadow-lg dark:border-gray-700 dark:bg-gray-800">
                <label className="flex w-full cursor-pointer items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-700">
                  <span>📎</span> Image / Video
                  <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden"
                    multiple
                    accept="image/png,image/jpeg,image/webp,video/mp4,video/quicktime"
                    onChange={(e) => { setMenuOpen(false); void handleFileSelect(e.target.files); }}
                  />
                </label>
                {(["code", "table", "formula"] as DraftKind[]).map((kind) => (
                  <button
                    key={kind}
                    type="button"
                    onClick={() => openDraft(kind)}
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-700"
                  >
                    <span>{ATTACHMENT_EMOJI[kind]}</span>
                    {kind.charAt(0).toUpperCase() + kind.slice(1)} snippet
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Text input */}
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={onKeyDown}
            rows={1}
            placeholder={
              uploading
                ? "Uploading..."
                : disabled
                ? "Waiting for response..."
                : "Ask anything or attach files..."
            }
            disabled={disabled || uploading}
            className="flex-1 resize-none rounded-xl border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900 shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:cursor-not-allowed disabled:bg-gray-100 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100 dark:disabled:bg-gray-900"
            style={{ minHeight: "42px", maxHeight: "160px" }}
          />

          {/* Send button */}
          <button
            type="submit"
            disabled={!canSend}
            className="flex h-10 items-center gap-1.5 rounded-xl bg-blue-600 px-4 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300 disabled:text-gray-500 sm:px-5"
          >
            {uploading ? (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M2.01 21 23 12 2.01 3 2 10l15 2-15 2z" />
              </svg>
            )}
            <span className="hidden sm:inline">{uploading ? "Uploading" : "Send"}</span>
          </button>
        </form>

        {/* Hint */}
        <p className="text-center text-[11px] text-gray-400 dark:text-gray-600">
          Max file size: {MAX_MB}MB &nbsp;·&nbsp; Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
