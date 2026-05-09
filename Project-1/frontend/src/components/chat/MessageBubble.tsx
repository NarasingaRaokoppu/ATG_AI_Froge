import ReactMarkdown from "react-markdown";

import { AttachmentPreview } from "../attachments/AttachmentPreview";
import { SourceCitation } from "../rag/SourceCitation";
import type { ChatMessage, GeneratedImage, RagDocument } from "../../types";

interface MessageBubbleProps {
  message: ChatMessage;
  onImageRegenerate?: (image: GeneratedImage) => void;
}

function resolveImageUrl(url?: string | null): string {
  if (!url) return "";
  if (/^https?:\/\//i.test(url)) return url;
  const base = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
  const origin = base.replace(/\/api\/?$/, "");
  return url.startsWith("/") ? `${origin}${url}` : `${origin}/${url}`;
}

export function MessageBubble({ message, onImageRegenerate }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const image = (message.metadata?.image as GeneratedImage | undefined) ?? undefined;
  const document =
    (message.metadata?.document as RagDocument | undefined) ?? undefined;
  const imageUrlFromMetadata =
    (message.metadata?.imageUrl as string | undefined) ?? image?.image_url;

  if (message.message_type === "image") {
    console.debug("[MessageBubble] image message detection", {
      id: message.id,
      hasImageMeta: Boolean(image),
      imageUrl: imageUrlFromMetadata,
    });
  }

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"} px-4 py-2`}>
      <div className="flex max-w-3xl flex-col gap-2">
        <div
          className={`rounded-2xl px-4 py-3 shadow-sm ${
            isUser
              ? "bg-blue-600 text-white rounded-br-sm"
              : "bg-gray-100 text-gray-900 rounded-bl-sm dark:bg-gray-800 dark:text-gray-100"
          }`}
        >
          {message.content ? (
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          ) : (
            <TypingIndicator />
          )}

          {message.attachments && message.attachments.length > 0 ? (
            <div className="mt-3">
              <AttachmentPreview attachments={message.attachments} />
            </div>
          ) : null}

          {message.status === "error" && message.error ? (
            <p className="mt-2 text-xs text-red-600 dark:text-red-400">{message.error}</p>
          ) : null}

          {message.status === "loading" ? (
            <div className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-gray-200/80 px-2 py-1 text-[11px] text-gray-600 dark:bg-gray-700/70 dark:text-gray-300">
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
              <span>Processing...</span>
            </div>
          ) : null}
        </div>

        {message.message_type === "image" && imageUrlFromMetadata ? (
          <article className="overflow-hidden rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900">
            {imageUrlFromMetadata ? (
              <img
                src={resolveImageUrl(imageUrlFromMetadata)}
                alt={image?.prompt || "Generated image"}
                loading="lazy"
                className="max-h-[420px] w-full object-cover"
              />
            ) : null}
            <div className="border-t border-gray-200 p-3 dark:border-gray-700">
              <p className="text-xs text-gray-600 dark:text-gray-300">{image?.prompt || message.content}</p>
              <div className="mt-2 flex flex-wrap gap-2">
                <a
                  href={resolveImageUrl(imageUrlFromMetadata)}
                  download
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-800"
                >
                  Download image
                </a>
                {onImageRegenerate && image ? (
                  <button
                    type="button"
                    onClick={() => onImageRegenerate(image)}
                    className="inline-flex rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-800"
                  >
                    Regenerate
                  </button>
                ) : null}
              </div>
            </div>
          </article>
        ) : null}

        {message.message_type === "pdf" ? (
          <article className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-900">
            <div className="text-xl">📕</div>
            <div className="flex-1 min-w-0">
              <p className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">{document?.filename ?? "PDF"}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {typeof document?.chunk_count === "number" ? `${document.chunk_count} chunks` : "Preparing document"}
                {typeof document?.file_size === "number"
                  ? ` · ${(document.file_size / 1024).toFixed(1)}KB`
                  : ""}
              </p>
            </div>
            <span
              className={`rounded-full px-2 py-1 text-xs font-medium ${
                document?.status === "processed"
                  ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                  : document?.status === "processing" || document?.status === "queued"
                  ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                  : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
              }`}
            >
              {document?.status ?? (message.status === "loading" ? "processing" : "unknown")}
            </span>
          </article>
        ) : null}

        {message.message_type === "rag_response" && message.citations?.length ? (
          <section className="space-y-2 rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-900">
            <p className="text-xs font-semibold text-gray-600 dark:text-gray-300">Sources</p>
            {message.citations.map((citation) => (
              <SourceCitation key={citation.chunk_id} citation={citation} />
            ))}
          </section>
        ) : null}

        <p className="px-1 text-[11px] text-gray-400 dark:text-gray-500">
          {message.created_at
            ? new Date(message.created_at).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })
            : ""}
        </p>
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 py-1">
      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.3s]" />
      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.15s]" />
      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400" />
    </div>
  );
}
