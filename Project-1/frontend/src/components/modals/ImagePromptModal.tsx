import { useEffect, useMemo, useState } from "react";

import type { ImageAspectRatio, ImageStyle } from "../../types";

interface ImagePromptModalProps {
  open: boolean;
  busy: boolean;
  onClose: () => void;
  onSubmit: (payload: {
    prompt: string;
    style: ImageStyle;
    aspect_ratio: ImageAspectRatio;
    enhance_prompt: boolean;
  }) => void;
}

const styles: Array<{ label: string; value: ImageStyle }> = [
  { label: "No Style", value: "none" },
  { label: "Photorealistic", value: "photorealistic" },
  { label: "Cinematic", value: "cinematic" },
  { label: "Anime", value: "anime" },
  { label: "Digital Art", value: "digital-art" },
  { label: "Watercolor", value: "watercolor" },
  { label: "Minimal", value: "minimal" },
];

const ratios: Array<{ label: string; value: ImageAspectRatio }> = [
  { label: "Square (1:1)", value: "1:1" },
  { label: "Landscape (16:9)", value: "16:9" },
  { label: "Portrait (9:16)", value: "9:16" },
  { label: "Classic (4:3)", value: "4:3" },
  { label: "Tall (3:4)", value: "3:4" },
];

export function ImagePromptModal({
  open,
  busy,
  onClose,
  onSubmit,
}: ImagePromptModalProps) {
  const [prompt, setPrompt] = useState("");
  const [style, setStyle] = useState<ImageStyle>("none");
  const [aspectRatio, setAspectRatio] = useState<ImageAspectRatio>("1:1");
  const [enhancePrompt, setEnhancePrompt] = useState(true);

  useEffect(() => {
    if (!open) return;
    const onEsc = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !busy) onClose();
    };
    window.addEventListener("keydown", onEsc);
    return () => window.removeEventListener("keydown", onEsc);
  }, [busy, onClose, open]);

  const canSubmit = useMemo(() => prompt.trim().length >= 3 && !busy, [prompt, busy]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-4">
      <div className="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl dark:border-slate-700 dark:bg-slate-900">
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              Generate AI Image
            </h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Prompt, style, and framing are sent to Gemini image generation.
            </p>
          </div>
          <button
            type="button"
            disabled={busy}
            onClick={onClose}
            className="rounded-md px-2 py-1 text-slate-500 hover:bg-slate-100 hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-60 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
          >
            Close
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Prompt
            </label>
            <textarea
              rows={4}
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              placeholder="A cinematic city skyline at sunrise with reflective rain puddles"
              className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
            />
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Style
              </label>
              <select
                value={style}
                onChange={(event) => setStyle(event.target.value as ImageStyle)}
                className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              >
                {styles.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Aspect Ratio
              </label>
              <select
                value={aspectRatio}
                onChange={(event) => setAspectRatio(event.target.value as ImageAspectRatio)}
                className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              >
                {ratios.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <label className="flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700 dark:bg-slate-800/70 dark:text-slate-200">
            <input
              type="checkbox"
              checked={enhancePrompt}
              onChange={(event) => setEnhancePrompt(event.target.checked)}
              className="h-4 w-4 rounded border-slate-300 text-cyan-600 focus:ring-cyan-500"
            />
            Enable prompt enhancement
          </label>
        </div>

        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={!canSubmit}
            onClick={() =>
              onSubmit({
                prompt: prompt.trim(),
                style,
                aspect_ratio: aspectRatio,
                enhance_prompt: enhancePrompt,
              })
            }
            className="rounded-lg bg-cyan-600 px-4 py-2 text-sm font-semibold text-white hover:bg-cyan-500 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {busy ? "Generating..." : "Generate"}
          </button>
        </div>
      </div>
    </div>
  );
}
