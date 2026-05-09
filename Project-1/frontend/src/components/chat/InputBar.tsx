import {
  useRef,
  useState,
  useEffect,
  type FormEvent,
  type KeyboardEvent,
} from "react";

import { AttachmentMenu } from "./AttachmentMenu";
import { useUploads } from "../../hooks/useUploads";
import type { ImageAspectRatio, ImageStyle, MessageAttachment } from "../../types";

const ATTACHMENT_EMOJI: Record<string, string> = {
  image: "🖼️",
  video: "🎥",
  code: "💻",
  table: "📊",
  formula: "∫",
  excel: "📈",
  docx: "📄",
  txt: "📝",
};

interface InputBarProps {
  disabled: boolean;
  activeThreadId: string | null;
  onSend: (payload: { message: string; attachments: MessageAttachment[] }) => void;
  onGenerateImage: (payload: {
    prompt: string;
    style: ImageStyle;
    aspect_ratio: ImageAspectRatio;
    enhance_prompt: boolean;
  }) => void;
  onUploadPdf: (files: File[]) => void;
}

export function InputBar({
  disabled,
  activeThreadId,
  onSend,
  onGenerateImage,
  onUploadPdf,
}: InputBarProps) {
  const [value, setValue] = useState("");
  const [attachments, setAttachments] = useState<MessageAttachment[]>([]);
  const { uploading, uploadError, uploadAttachments } = useUploads();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-focus on mount
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    const trimmed = value.trim();
    if ((!trimmed && attachments.length === 0) || disabled || uploading) return;
    onSend({ message: trimmed || "Please analyze the attachments.", attachments });
    setValue("");
    setAttachments([]);
    textareaRef.current?.focus();
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

        {/* Main input row */}
        <form onSubmit={submit} className="flex items-end gap-2">
          {/* Unified attachment menu */}
          <AttachmentMenu
            disabled={disabled}
            activeThreadId={activeThreadId}
            busy={uploading || disabled}
            error={uploadError}
            onSelectFiles={(files) => {
              void (async () => {
                try {
                  const uploaded = await uploadAttachments(files);
                  setAttachments((prev) => [...prev, ...uploaded]);
                } catch {
                  // Error state is exposed by useUploads.
                }
              })();
            }}
            onSelectPdf={(files) => {
              onUploadPdf(files);
            }}
            onGenerateImage={(payload) => {
              onGenerateImage(payload);
            }}
            onDraftAttached={(draft) => {
              setAttachments((prev) => [...prev, draft]);
            }}
          />

          {/* Text input */}
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={onKeyDown}
            rows={1}
            placeholder={
              disabled
                ? "Waiting for response..."
                : uploading
                ? "Uploading files..."
                : "Ask anything or use the + button for attachments..."
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
          Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
