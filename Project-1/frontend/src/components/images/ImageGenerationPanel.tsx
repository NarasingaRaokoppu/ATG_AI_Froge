import { useMemo, useState } from "react";

import { imageApi } from "../../lib/endpoints";
import type {
  GeneratedImage,
  ImageAspectRatio,
  ImageStyle,
} from "../../types";
import { ImageGallery } from "./ImageGallery";
import { ImagePromptModal } from "../modals/ImagePromptModal";

interface ImageGenerationPanelProps {
  activeThreadId: string | null;
  images: GeneratedImage[];
  loading: boolean;
  onThreadResolved: (threadId: string) => void;
  onImagesUpdated: (images: GeneratedImage[]) => void;
}

export function ImageGenerationPanel({
  activeThreadId,
  images,
  loading,
  onThreadResolved,
  onImagesUpdated,
}: ImageGenerationPanelProps) {
  const [modalOpen, setModalOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [busyImageId, setBusyImageId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const orderedImages = useMemo(
    () => [...images].sort((a, b) => +new Date(b.created_at) - +new Date(a.created_at)),
    [images]
  );

  const refreshThreadImages = async (threadId: string) => {
    const data = await imageApi.listByThread(threadId);
    onImagesUpdated(data);
  };

  const handleGenerate = async (payload: {
    prompt: string;
    style: ImageStyle;
    aspect_ratio: ImageAspectRatio;
    enhance_prompt: boolean;
  }) => {
    setBusy(true);
    setError(null);
    try {
      const response = await imageApi.generate({
        prompt: payload.prompt,
        thread_id: activeThreadId,
        style: payload.style,
        aspect_ratio: payload.aspect_ratio,
        enhance_prompt: payload.enhance_prompt,
      });

      onThreadResolved(response.thread_id);
      await refreshThreadImages(response.thread_id);
      setModalOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Image generation failed");
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async (imageId: string) => {
    if (!activeThreadId) return;
    setBusyImageId(imageId);
    setError(null);
    try {
      await imageApi.remove(imageId);
      await refreshThreadImages(activeThreadId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setBusyImageId(null);
    }
  };

  const handleRegenerate = async (image: GeneratedImage) => {
    setBusyImageId(image.id);
    setError(null);
    try {
      const response = await imageApi.regenerate({
        image_id: image.id,
        prompt_override: image.prompt,
        style: (image.style as ImageStyle | null) ?? undefined,
        aspect_ratio: (image.aspect_ratio as ImageAspectRatio | null) ?? undefined,
        enhance_prompt: true,
      });
      onThreadResolved(response.thread_id);
      await refreshThreadImages(response.thread_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Regeneration failed");
    } finally {
      setBusyImageId(null);
    }
  };

  return (
    <section className="mb-3 rounded-xl border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-950/60">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            AI Image Studio
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Gemini image generation with thread-scoped history.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setModalOpen(true)}
          className="rounded-lg bg-cyan-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-cyan-500"
        >
          New Image
        </button>
      </div>

      {error ? (
        <p className="mb-2 rounded-md bg-rose-50 px-2 py-1 text-xs text-rose-700 dark:bg-rose-950/40 dark:text-rose-300">
          {error}
        </p>
      ) : null}

      <ImageGallery
        images={orderedImages}
        loading={loading}
        busyId={busyImageId}
        onDelete={handleDelete}
        onRegenerate={handleRegenerate}
      />

      <ImagePromptModal
        open={modalOpen}
        busy={busy}
        onClose={() => setModalOpen(false)}
        onSubmit={handleGenerate}
      />
    </section>
  );
}
