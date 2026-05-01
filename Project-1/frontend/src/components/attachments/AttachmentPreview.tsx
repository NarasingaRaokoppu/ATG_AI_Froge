import type { MessageAttachment } from "../../types";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api";
const API_ORIGIN = API_BASE_URL.replace(/\/api\/?$/, "");

function resolveAttachmentUrl(url: string | null | undefined): string {
  if (!url) return "";
  if (/^https?:\/\//i.test(url)) return url;
  if (url.startsWith("/")) return `${API_ORIGIN}${url}`;
  return `${API_ORIGIN}/${url}`;
}

interface AttachmentPreviewProps {
  attachments: MessageAttachment[];
  onRemove?: (index: number) => void;
}

function renderTable(raw: string) {
  try {
    const parsed = JSON.parse(raw);
    const rows: Record<string, unknown>[] = Array.isArray(parsed)
      ? parsed
      : [parsed];
    if (!rows.length) return null;
    const keys = Object.keys(rows[0]);
    if (!keys.length) return null;

    return (
      <div className="overflow-x-auto rounded-md border border-gray-200 dark:border-gray-700">
        <table className="min-w-full text-xs">
          <thead className="bg-gray-100 dark:bg-gray-800">
            <tr>
              {keys.map((k) => (
                <th key={k} className="px-2 py-1 text-left font-semibold">
                  {k}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 5).map((row, i) => (
              <tr key={i} className="border-t border-gray-200 dark:border-gray-700">
                {keys.map((k) => (
                  <td key={k} className="px-2 py-1 align-top">
                    {String(row[k] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  } catch {
    return (
      <pre className="max-h-40 overflow-auto rounded-md bg-gray-100 p-2 text-xs dark:bg-gray-800">
        {raw}
      </pre>
    );
  }
}

const TYPE_LABEL: Record<string, string> = {
  image: "🖼️ Image",
  video: "🎥 Video",
  code: "💻 Code",
  table: "📊 Table",
  formula: "∫ Formula",
};

export function AttachmentPreview({ attachments, onRemove }: AttachmentPreviewProps) {
  if (attachments.length === 0) return null;

  return (
    /* Horizontal scroll on mobile, wrapping grid on larger screens */
    <div className="flex gap-2 overflow-x-auto pb-1 sm:grid sm:grid-cols-2 sm:overflow-x-visible sm:pb-0">
      {attachments.map((a, idx) => {
        const key = `${a.attachment_type}-${idx}-${a.name ?? ""}`;
        return (
          <div
            key={key}
            className="relative min-w-[220px] flex-shrink-0 rounded-xl border border-gray-200 bg-white p-2 text-xs sm:min-w-0 sm:flex-shrink dark:border-gray-700 dark:bg-gray-900"
          >
            {/* Type badge */}
            <span className="mb-1.5 inline-block rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-semibold text-gray-600 dark:bg-gray-800 dark:text-gray-300">
              {TYPE_LABEL[a.attachment_type] ?? a.attachment_type}
              {a.name ? ` · ${a.name}` : ""}
            </span>

            {onRemove && (
              <button
                type="button"
                onClick={() => onRemove(idx)}
                className="absolute right-1 top-1 rounded p-1 text-gray-400 hover:bg-gray-200 hover:text-gray-700 dark:hover:bg-gray-700 dark:hover:text-gray-100"
                aria-label="Remove attachment"
              >
                ✕
              </button>
            )}

            {a.attachment_type === "image" && a.attachment_url ? (
              <img
                src={resolveAttachmentUrl(a.attachment_url)}
                loading="lazy"
                alt={a.name || "Uploaded image"}
                className="mt-0.5 h-36 w-full rounded-md object-cover"
              />
            ) : null}

            {a.attachment_type === "video" && a.attachment_url ? (
              <video
                src={resolveAttachmentUrl(a.attachment_url)}
                controls
                className="mt-0.5 h-36 w-full rounded-md bg-black"
                preload="metadata"
              />
            ) : null}

            {a.attachment_type === "code" ? (
              <pre className="mt-0.5 max-h-44 overflow-auto rounded-md bg-gray-100 p-2 text-xs dark:bg-gray-800">
                {a.content || ""}
              </pre>
            ) : null}

            {a.attachment_type === "table" ? (
              <div className="mt-0.5">{renderTable(a.content || "")}</div>
            ) : null}

            {a.attachment_type === "formula" ? (
              <pre className="mt-0.5 rounded-md bg-gray-100 p-2 text-xs dark:bg-gray-800">
                {a.content || ""}
              </pre>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
