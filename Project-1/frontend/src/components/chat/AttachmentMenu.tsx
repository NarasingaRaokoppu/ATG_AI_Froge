import { useEffect, useRef, useState, type KeyboardEvent } from "react";

import type { ImageAspectRatio, ImageStyle, MessageAttachment } from "../../types";

type AttachmentMenuMode =
  | "closed"
  | "main"
  | "pdf"
  | "image"
  | "code"
  | "table"
  | "formula";

const ATTACHMENT_EMOJI: Record<string, string> = {
  image: "🖼️",
  video: "🎥",
  code: "💻",
  table: "📊",
  formula: "∫",
  excel: "📈",
  docx: "📄",
  txt: "📝",
  pdf: "📕",
};

interface AttachmentMenuProps {
  disabled: boolean;
  activeThreadId: string | null;
  busy?: boolean;
  error?: string | null;
  onSelectFiles: (files: File[]) => void;
  onSelectPdf: (files: File[]) => void;
  onGenerateImage: (payload: {
    prompt: string;
    style: ImageStyle;
    aspect_ratio: ImageAspectRatio;
    enhance_prompt: boolean;
  }) => void;
  onDraftAttached?: (attachment: MessageAttachment) => void;
}

export function AttachmentMenu({
  disabled,
  activeThreadId,
  busy = false,
  error,
  onSelectFiles,
  onSelectPdf,
  onGenerateImage,
  onDraftAttached,
}: AttachmentMenuProps) {
  const [mode, setMode] = useState<AttachmentMenuMode>("closed");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pdfInputRef = useRef<HTMLInputElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const [draftContent, setDraftContent] = useState("");
  const draftKind = mode as "code" | "table" | "formula" | null;

  const [imagePrompt, setImagePrompt] = useState("");
  const [imageStyle, setImageStyle] = useState<ImageStyle>("digital-art");
  const [imageAspectRatio, setImageAspectRatio] = useState<ImageAspectRatio>("1:1");
  const [enhancePrompt, setEnhancePrompt] = useState(true);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMode("closed");
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const onFilesChanged = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    onSelectFiles(Array.from(files));
    if (fileInputRef.current) fileInputRef.current.value = "";
    setMode("closed");
  };

  const onPdfChanged = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    onSelectPdf(Array.from(files));
    if (pdfInputRef.current) pdfInputRef.current.value = "";
    setMode("closed");
  };

  const handleGenerateImage = () => {
    if (!imagePrompt.trim()) return;

    onGenerateImage({
      prompt: imagePrompt.trim(),
      style: imageStyle,
      aspect_ratio: imageAspectRatio,
      enhance_prompt: enhancePrompt,
    });
    setImagePrompt("");
    setMode("closed");
  };

  const handleImagePromptKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleGenerateImage();
    }
  };

  const commitDraft = () => {
    const content = draftContent.trim();
    if (!content || !draftKind) return;

    onDraftAttached?.({
      attachment_type: draftKind,
      content,
      name: `${draftKind}-snippet`,
    });
    setDraftContent("");
    setMode("closed");
  };

  const isMainMenuOpen = mode === "main";
  const isPdfMode = mode === "pdf";
  const isImageMode = mode === "image";
  const isDraftMode = mode === "code" || mode === "table" || mode === "formula";

  return (
    <div className="relative" ref={menuRef}>
      <button
        type="button"
        onClick={() => setMode(isMainMenuOpen ? "closed" : "main")}
        disabled={disabled || busy}
        className="flex h-10 w-10 items-center justify-center rounded-xl border border-gray-300 bg-white text-gray-600 transition hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
        aria-label="Add attachment"
        title="Upload files, PDFs, generate images, or add code snippets"
      >
        <span className="text-lg font-light leading-none">+</span>
      </button>

      {isMainMenuOpen && (
        <div className="absolute bottom-12 left-0 z-20 w-48 rounded-xl border border-gray-200 bg-white py-1 shadow-lg dark:border-gray-700 dark:bg-gray-800">
          <button
            type="button"
            onClick={() => setMode("pdf")}
            className="flex w-full items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-700"
          >
            <span>📕</span> Upload PDF
          </button>
          <button
            type="button"
            onClick={() => setMode("image")}
            className="flex w-full items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-700"
          >
            <span>🎨</span> Generate Image
          </button>
          <label className="flex w-full cursor-pointer items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-700">
            <span>📎</span> Upload Files
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              multiple
              accept="image/png,image/jpeg,image/webp,video/mp4,video/quicktime,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,application/vnd.ms-excel.sheet.macroEnabled.12,text/csv,.csv,.xlsx,.xls,.xlsm,.xlsb,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/msword,.docx,.doc,text/plain,.txt"
              onChange={(e) => onFilesChanged(e.target.files)}
            />
          </label>
          <hr className="my-1 border-gray-200 dark:border-gray-700" />
          {(["code", "table", "formula"] as const).map((kind) => (
            <button
              key={kind}
              type="button"
              onClick={() => setMode(kind)}
              className="flex w-full items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-700"
            >
              <span>{ATTACHMENT_EMOJI[kind]}</span>
              {kind.charAt(0).toUpperCase() + kind.slice(1)} snippet
            </button>
          ))}
        </div>
      )}

      {isPdfMode && (
        <div className="absolute bottom-12 left-0 z-20 w-64 rounded-xl border border-gray-200 bg-white p-3 shadow-lg dark:border-gray-700 dark:bg-gray-800">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Upload PDF</h3>
            <button
              type="button"
              onClick={() => setMode("main")}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              ←
            </button>
          </div>

          {error ? (
            <p className="mb-2 rounded-md bg-red-50 px-2 py-1 text-xs text-red-700 dark:bg-red-950/40 dark:text-red-300">
              {error}
            </p>
          ) : null}

          {!activeThreadId ? (
            <p className="mb-2 text-xs text-amber-700 dark:text-amber-300">
              A new thread will be created automatically when you upload.
            </p>
          ) : null}

          <label className="flex w-full cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 px-4 py-6 text-center dark:border-gray-600 dark:bg-gray-900">
            <span className="text-2xl">📄</span>
            <span className="mt-1 text-xs font-medium text-gray-700 dark:text-gray-300">Click to upload PDF</span>
            <input
              ref={pdfInputRef}
              type="file"
              className="hidden"
              accept=".pdf,application/pdf"
              onChange={(e) => onPdfChanged(e.target.files)}
            />
          </label>
        </div>
      )}

      {isImageMode && (
        <div className="absolute bottom-12 left-0 z-20 w-80 rounded-xl border border-gray-200 bg-white p-3 shadow-lg dark:border-gray-700 dark:bg-gray-800">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Generate Image</h3>
            <button
              type="button"
              onClick={() => setMode("main")}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              ←
            </button>
          </div>

          {error ? (
            <p className="mb-2 rounded-md bg-red-50 px-2 py-1 text-xs text-red-700 dark:bg-red-950/40 dark:text-red-300">
              {error}
            </p>
          ) : null}

          <div className="space-y-2">
            <input
              type="text"
              value={imagePrompt}
              onChange={(e) => setImagePrompt(e.target.value)}
              onKeyDown={handleImagePromptKeyDown}
              placeholder="Describe the image you want to generate..."
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-xs text-gray-900 placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
            />

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-[11px] font-medium text-gray-700 dark:text-gray-300">Style</label>
                <select
                  value={imageStyle}
                  onChange={(e) => setImageStyle(e.target.value as ImageStyle)}
                  className="w-full rounded-lg border border-gray-300 bg-white px-2 py-1 text-xs text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                >
                  <option value="photorealistic">Photorealistic</option>
                  <option value="cinematic">Cinematic</option>
                  <option value="anime">Anime</option>
                  <option value="digital-art">Digital Art</option>
                  <option value="watercolor">Watercolor</option>
                  <option value="minimal">Minimal</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-medium text-gray-700 dark:text-gray-300">Aspect</label>
                <select
                  value={imageAspectRatio}
                  onChange={(e) => setImageAspectRatio(e.target.value as ImageAspectRatio)}
                  className="w-full rounded-lg border border-gray-300 bg-white px-2 py-1 text-xs text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
                >
                  <option value="1:1">1:1</option>
                  <option value="16:9">16:9</option>
                  <option value="9:16">9:16</option>
                  <option value="4:3">4:3</option>
                  <option value="3:4">3:4</option>
                </select>
              </div>
            </div>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={enhancePrompt}
                onChange={(e) => setEnhancePrompt(e.target.checked)}
                className="h-3 w-3 rounded border-gray-300"
              />
              <span className="text-xs text-gray-700 dark:text-gray-300">Enhance prompt</span>
            </label>

            <button
              type="button"
              onClick={handleGenerateImage}
              disabled={busy || !imagePrompt.trim()}
              className="w-full rounded-lg bg-cyan-600 px-3 py-2 text-xs font-semibold text-white hover:bg-cyan-500 disabled:bg-gray-300 disabled:text-gray-500"
            >
              {busy ? "Generating..." : "Generate"}
            </button>
          </div>
        </div>
      )}

      {isDraftMode && draftKind ? (
        <div className="absolute bottom-12 left-0 z-20 w-80 rounded-xl border border-gray-200 bg-white p-3 shadow-lg dark:border-gray-700 dark:bg-gray-800">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              {ATTACHMENT_EMOJI[draftKind]} Add {draftKind}
            </h3>
            <button
              type="button"
              onClick={() => setMode("main")}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
            >
              ←
            </button>
          </div>

          <textarea
            autoFocus
            value={draftContent}
            onChange={(e) => setDraftContent(e.target.value)}
            rows={6}
            placeholder={
              draftKind === "code"
                ? "Paste your code here..."
                : draftKind === "table"
                ? 'Paste JSON array: [{"col": "val"}, ...]'
                : "Enter formula or expression..."
            }
            className="w-full resize-y rounded-lg border border-gray-300 bg-white px-3 py-2 font-mono text-xs focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
          />

          <div className="mt-2 flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setMode("main")}
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
      ) : null}
    </div>
  );
}
