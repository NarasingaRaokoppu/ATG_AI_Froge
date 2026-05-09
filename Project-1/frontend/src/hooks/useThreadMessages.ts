import { useCallback, useEffect, useMemo, useState } from "react";

import { messageApi } from "../lib/endpoints";
import { imageService } from "../services/imageService";
import { ragService } from "../services/ragService";
import type { ChatMessage, GeneratedImage, RagDocument } from "../types";

function toEpoch(value?: string | null): number {
  if (!value) return 0;
  const t = Date.parse(value);
  return Number.isNaN(t) ? 0 : t;
}

const newId = () =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2);

function normalizeImageToMessage(img: GeneratedImage): ChatMessage {
  return {
    id: `img-${img.id}`,
    role: "assistant",
    content: img.prompt || "Generated image",
    message_type: "image",
    created_at: img.created_at,
    metadata: {
      image: {
        ...img,
        image_url: img.image_url,
      },
      imageUrl: img.image_url,
      threadId: img.thread_id,
    },
  };
}

export function useThreadMessages(activeThreadId: string | null) {
  const [baseMessages, setBaseMessages] = useState<ChatMessage[]>([]);
  const [generatedImages, setGeneratedImages] = useState<GeneratedImage[]>([]);
  const [ragDocuments, setRagDocuments] = useState<RagDocument[]>([]);
  const [loading, setLoading] = useState(false);

  const refreshGeneratedImages = useCallback(async () => {
    if (!activeThreadId) return;
    const images = await imageService.listByThread(activeThreadId);
    console.debug("[useThreadMessages] image fetch response", {
      threadId: activeThreadId,
      count: images.length,
      statuses: images.map((i) => i.status),
    });
    setGeneratedImages(images);
  }, [activeThreadId]);

  const refreshRagDocuments = useCallback(async () => {
    if (!activeThreadId) return;
    const docs = await ragService.listDocuments(activeThreadId);
    setRagDocuments(docs);
  }, [activeThreadId]);

  const refreshThreadState = useCallback(async () => {
    if (!activeThreadId) {
      setBaseMessages([]);
      setGeneratedImages([]);
      setRagDocuments([]);
      return;
    }

    setLoading(true);
    try {
      const [messagesResult, imagesResult, docsResult] = await Promise.allSettled([
        messageApi.list(activeThreadId),
        imageService.listByThread(activeThreadId),
        ragService.listDocuments(activeThreadId),
      ]);

      if (messagesResult.status === "fulfilled") {
        const dtos = messagesResult.value;
        setBaseMessages(
          dtos.map((m) => ({
            id: m.id,
            role: m.role,
            content: m.content,
            attachments: m.attachments ?? [],
            message_type: "text",
            created_at: m.created_at,
          }))
        );
      } else {
        console.warn("[useThreadMessages] message fetch failed", messagesResult.reason);
        setBaseMessages([]);
      }

      if (imagesResult.status === "fulfilled") {
        const images = imagesResult.value;
        console.debug("[useThreadMessages] image fetch response", {
          threadId: activeThreadId,
          count: images.length,
          ids: images.map((i) => i.id),
        });
        setGeneratedImages(images);
      } else {
        console.warn("[useThreadMessages] image fetch failed", imagesResult.reason);
        setGeneratedImages([]);
      }

      if (docsResult.status === "fulfilled") {
        setRagDocuments(docsResult.value);
      } else {
        console.warn("[useThreadMessages] rag document fetch failed", docsResult.reason);
        setRagDocuments([]);
      }
    } finally {
      setLoading(false);
    }
  }, [activeThreadId]);

  useEffect(() => {
    void refreshThreadState();
  }, [refreshThreadState]);

  // Poll document status while any document is still processing.
  useEffect(() => {
    if (!activeThreadId) return;
    const shouldPoll = ragDocuments.some(
      (doc) => doc.status === "queued" || doc.status === "processing"
    );
    if (!shouldPoll) return;

    const timer = window.setInterval(() => {
      void refreshRagDocuments();
    }, 4000);

    return () => window.clearInterval(timer);
  }, [activeThreadId, ragDocuments, refreshRagDocuments]);

  const timelineMessages = useMemo(() => {
    const representedImageIds = new Set<string>();
    const representedDocumentIds = new Set<string>();
    for (const msg of baseMessages) {
      const imageFromMetadata =
        (msg.metadata?.image as { id?: string } | undefined)?.id ?? undefined;
      if (imageFromMetadata) representedImageIds.add(imageFromMetadata);

      const docFromMetadata =
        (msg.metadata?.document as { id?: string } | undefined)?.id ?? undefined;
      if (docFromMetadata) representedDocumentIds.add(docFromMetadata);

      const attachments = msg.attachments ?? [];
      for (const att of attachments) {
        const maybeId =
          (att.metadata?.generated_image_id as string | undefined) ??
          (att.metadata?.generatedImageId as string | undefined);
        if (maybeId) representedImageIds.add(maybeId);

        const maybeDocId =
          (att.metadata?.document_id as string | undefined) ??
          (att.metadata?.documentId as string | undefined);
        if (maybeDocId) representedDocumentIds.add(maybeDocId);
      }
    }

    const imageMessages: ChatMessage[] = generatedImages
      .filter((img) => img.status !== "deleted")
      .filter((img) => !representedImageIds.has(img.id))
      .map(normalizeImageToMessage);

    const seenDocIds = new Set<string>();
    const documentMessages: ChatMessage[] = ragDocuments
      .filter((doc) => {
        if (seenDocIds.has(doc.id)) return false;
        seenDocIds.add(doc.id);
        return !representedDocumentIds.has(doc.id);
      })
      .map((doc) => ({
        id: `pdf-${doc.id}`,
        role: "assistant",
        content:
          doc.status === "processed"
            ? `PDF indexed successfully: ${doc.filename}`
            : doc.status === "failed"
            ? `PDF processing failed: ${doc.filename}`
            : `PDF upload received: ${doc.filename} (${doc.status})`,
        message_type: "pdf",
        created_at: doc.upload_time,
        metadata: { document: doc },
      }));

    const combined = [...baseMessages, ...imageMessages, ...documentMessages];
    combined.sort((a, b) => toEpoch(a.created_at) - toEpoch(b.created_at));

    console.debug("[useThreadMessages] merged timeline output", {
      total: combined.length,
      text: combined.filter((m) => m.message_type === "text").length,
      image: combined.filter((m) => m.message_type === "image").length,
      pdf: combined.filter((m) => m.message_type === "pdf").length,
    });

    return combined;
  }, [baseMessages, generatedImages, ragDocuments]);

  const appendBaseMessage = useCallback((message: ChatMessage) => {
    setBaseMessages((prev) => [
      ...prev,
      {
        ...message,
        created_at: message.created_at ?? new Date().toISOString(),
      },
    ]);
  }, []);

  const patchBaseMessage = useCallback(
    (messageId: string, updater: (prev: ChatMessage) => ChatMessage) => {
      setBaseMessages((prev) =>
        prev.map((msg) => (msg.id === messageId ? updater(msg) : msg))
      );
    },
    []
  );

  return {
    loading,
    timelineMessages,
    baseMessages,
    generatedImages,
    ragDocuments,
    refreshThreadState,
    refreshGeneratedImages,
    refreshRagDocuments,
    setBaseMessages,
    appendBaseMessage,
    patchBaseMessage,
    newId,
  };
}
