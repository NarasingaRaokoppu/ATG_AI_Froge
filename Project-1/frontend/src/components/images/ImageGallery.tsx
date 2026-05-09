import type { GeneratedImage } from "../../types";

interface ImageGalleryProps {
  images: GeneratedImage[];
  loading: boolean;
  busyId: string | null;
  onDelete: (imageId: string) => void;
  onRegenerate: (image: GeneratedImage) => void;
}

const BACKEND_ORIGIN = (import.meta.env.VITE_API_URL || "http://localhost:8000/api").replace(/\/api\/?$/, "");

function absoluteUrl(url: string) {
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  return `${BACKEND_ORIGIN}${url.startsWith("/") ? "" : "/"}${url}`;
}

export function ImageGallery({
  images,
  loading,
  busyId,
  onDelete,
  onRegenerate,
}: ImageGalleryProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {Array.from({ length: 4 }).map((_, idx) => (
          <div
            key={idx}
            className="h-56 animate-pulse rounded-xl border border-slate-200 bg-slate-100 dark:border-slate-800 dark:bg-slate-900"
          />
        ))}
      </div>
    );
  }

  if (images.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-5 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
        No generated images yet for this thread.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {images.map((image) => (
        <article
          key={image.id}
          className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900"
        >
          <img
            src={absoluteUrl(image.image_url)}
            alt={image.prompt}
            className="h-56 w-full object-cover"
            loading="lazy"
          />

          <div className="space-y-2 p-3">
            <p className="line-clamp-2 text-sm text-slate-700 dark:text-slate-200">
              {image.prompt}
            </p>

            <div className="flex flex-wrap gap-1">
              {image.style ? (
                <span className="rounded-full bg-cyan-50 px-2 py-0.5 text-xs font-medium text-cyan-700 dark:bg-cyan-950/40 dark:text-cyan-300">
                  {image.style}
                </span>
              ) : null}
              {image.aspect_ratio ? (
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                  {image.aspect_ratio}
                </span>
              ) : null}
            </div>

            <div className="flex items-center justify-between gap-2">
              <a
                href={absoluteUrl(image.image_url)}
                download
                className="rounded-md border border-slate-300 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
              >
                Download
              </a>

              <div className="flex gap-1.5">
                <button
                  type="button"
                  disabled={busyId === image.id}
                  onClick={() => onRegenerate(image)}
                  className="rounded-md bg-cyan-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-cyan-500 disabled:cursor-not-allowed disabled:bg-slate-400"
                >
                  Retry
                </button>
                <button
                  type="button"
                  disabled={busyId === image.id}
                  onClick={() => onDelete(image.id)}
                  className="rounded-md border border-rose-300 px-2.5 py-1 text-xs font-medium text-rose-600 hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-rose-900 dark:text-rose-300 dark:hover:bg-rose-950/40"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}
