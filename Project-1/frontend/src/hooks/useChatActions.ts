import { useCallback, useRef, useState } from "react";

import { threadApi } from "../lib/endpoints";
import { chatService } from "../services/chatService";
import { imageService } from "../services/imageService";
import { ragService } from "../services/ragService";
import type {
  ChatMessage,
  ImageAspectRatio,
  ImageStyle,
  MessageAttachment,
  RagDocument,
} from "../types";

function startsWithImageCommand(text: string): boolean {
  const normalized = text.trim().toLowerCase();
  return (
    normalized.startsWith("generate image") ||
    normalized.startsWith("create image") ||
    normalized.startsWith("generate a") ||
    normalized.startsWith("create a")
  );
}

function stripImageCommand(text: string): string {
  return text
    .replace(/^generate image\s*/i, "")
    .replace(/^create image\s*/i, "")
    .replace(/^generate\s*/i, "")
    .replace(/^create\s*/i, "")
    .trim();
}

const defaultImageStyle: ImageStyle = "digital-art";
const defaultAspectRatio: ImageAspectRatio = "1:1";

interface UseChatActionsParams {
  activeThreadId: string | null;
  ragDocuments: RagDocument[];
  setActiveThreadId: (threadId: string | null) => void;
  refreshThreads: () => Promise<unknown>;
  refreshGeneratedImages: () => Promise<void>;
  refreshRagDocuments: () => Promise<void>;
  appendBaseMessage: (message: ChatMessage) => void;
  patchBaseMessage: (
    messageId: string,
    updater: (prev: ChatMessage) => ChatMessage
  ) => void;
  newId: () => string;
}

export function useChatActions({
  activeThreadId,
  ragDocuments,
  setActiveThreadId,
  refreshThreads,
  refreshGeneratedImages,
  refreshRagDocuments,
  appendBaseMessage,
  patchBaseMessage,
  newId,
}: UseChatActionsParams) {
  const [isBusy, setIsBusy] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const ensureThread = useCallback(async (): Promise<string | null> => {
    if (activeThreadId) return activeThreadId;
    const created = await threadApi.create(null);
    setActiveThreadId(created.id);
    console.debug("[useChatActions] created thread", created.id);
    await refreshThreads();
    return created.id;
  }, [activeThreadId, setActiveThreadId, refreshThreads]);

  const handleImageGeneration = useCallback(
    async (params: {
      prompt: string;
      style?: ImageStyle;
      aspect_ratio?: ImageAspectRatio;
      enhance_prompt?: boolean;
      echoUserMessage?: boolean;
    }) => {
      const prompt = params.prompt.trim();
      if (!prompt) return;

      if (params.echoUserMessage !== false) {
        appendBaseMessage({
          id: newId(),
          role: "user",
          content: `Generate image: ${prompt}`,
          message_type: "text",
          created_at: new Date().toISOString(),
        });
      }

      const assistantId = newId();
      appendBaseMessage({
        id: assistantId,
        role: "assistant",
        content: "Generating image...",
        message_type: "image",
        status: "loading",
        pending: true,
        created_at: new Date().toISOString(),
      });

      setIsBusy(true);
      try {
        const response = await imageService.generate({
          prompt,
          thread_id: activeThreadId,
          style: params.style ?? defaultImageStyle,
          aspect_ratio: params.aspect_ratio ?? defaultAspectRatio,
          enhance_prompt: params.enhance_prompt ?? true,
        });

        if (response.thread_id !== activeThreadId) {
          setActiveThreadId(response.thread_id);
        }

        await refreshGeneratedImages();
        await refreshThreads();

        patchBaseMessage(assistantId, (prev) => ({
          ...prev,
          content: prompt,
          message_type: "image",
          status: "success",
          pending: false,
          metadata: { image: response.image },
        }));
      } catch (err) {
        const text = err instanceof Error ? err.message : "Image generation failed";
        patchBaseMessage(assistantId, (prev) => ({
          ...prev,
          content: `Image generation failed: ${text}`,
          status: "error",
          error: text,
          pending: false,
        }));
      } finally {
        setIsBusy(false);
      }
    },
    [
      activeThreadId,
      appendBaseMessage,
      newId,
      patchBaseMessage,
      refreshGeneratedImages,
      refreshThreads,
      setActiveThreadId,
    ]
  );

  const handlePdfUpload = useCallback(
    async (files: File[]) => {
      if (files.length === 0) return;
      const threadId = await ensureThread();
      if (!threadId) return;

      setIsBusy(true);
      try {
        for (const file of files) {
          const msgId = newId();
          appendBaseMessage({
            id: msgId,
            role: "assistant",
            content: `Uploading PDF: ${file.name}`,
            message_type: "pdf",
            status: "loading",
            pending: true,
            created_at: new Date().toISOString(),
            metadata: {
              document: {
                id: `pending-${msgId}`,
                user_id: "",
                thread_id: threadId,
                filename: file.name,
                file_size: file.size,
                status: "processing",
                upload_time: new Date().toISOString(),
                chunk_count: 0,
                embedding_model: "",
              },
            },
          });

          try {
            const response = await ragService.uploadPdf(threadId, file);
            patchBaseMessage(msgId, (prev) => ({
              ...prev,
              content: `PDF uploaded: ${response.document.filename}. Indexing started.`,
              message_type: "pdf",
              status: "success",
              pending: false,
              metadata: { document: response.document },
            }));
          } catch (err) {
            const text = err instanceof Error ? err.message : "PDF upload failed";
            patchBaseMessage(msgId, (prev) => ({
              ...prev,
              content: `PDF upload failed for ${file.name}: ${text}`,
              message_type: "pdf",
              status: "error",
              error: text,
              pending: false,
            }));
          }
        }

        await refreshRagDocuments();
        await refreshThreads();
      } finally {
        setIsBusy(false);
      }
    },
    [
      appendBaseMessage,
      ensureThread,
      newId,
      patchBaseMessage,
      refreshRagDocuments,
      refreshThreads,
    ]
  );

  const handleSendMessage = useCallback(
    async (payload: { message: string; attachments: MessageAttachment[] }) => {
      if (isBusy) return;

      const text = payload.message.trim();
      const attachments = payload.attachments;
      if (!text && attachments.length === 0) return;

      const userMsg: ChatMessage = {
        id: newId(),
        role: "user",
        content: text,
        attachments,
        message_type: "text",
        created_at: new Date().toISOString(),
      };
      appendBaseMessage(userMsg);

      const processedDocs = ragDocuments.filter((d) => d.status === "processed");
      const useImageAction = text.length > 0 && startsWithImageCommand(text);
      const useRagAction = !useImageAction && processedDocs.length > 0 && text.length > 0;

      console.debug("[useChatActions] action detection", {
        useImageAction,
        useRagAction,
        threadId: activeThreadId,
        docs: processedDocs.length,
      });

      if (useImageAction) {
        await handleImageGeneration({
          prompt: stripImageCommand(text) || text,
          echoUserMessage: false,
        });
        return;
      }

      if (useRagAction && activeThreadId) {
        const assistantId = newId();
        appendBaseMessage({
          id: assistantId,
          role: "assistant",
          content: "Searching indexed PDFs...",
          message_type: "rag_response",
          status: "loading",
          pending: true,
          created_at: new Date().toISOString(),
        });

        setIsBusy(true);
        try {
          const response = await ragService.chat({
            thread_id: activeThreadId,
            question: text,
            document_ids: processedDocs.map((d) => d.id),
          });

          patchBaseMessage(assistantId, (prev) => ({
            ...prev,
            content: response.answer,
            message_type: "rag_response",
            status: "success",
            pending: false,
            citations: response.citations,
            metadata: {
              grounded: response.grounded,
              confidence: response.confidence,
            },
          }));
        } catch (err) {
          const errorText = err instanceof Error ? err.message : "RAG request failed";
          patchBaseMessage(assistantId, (prev) => ({
            ...prev,
            content: `RAG request failed: ${errorText}`,
            status: "error",
            error: errorText,
            pending: false,
          }));
        } finally {
          setIsBusy(false);
        }

        return;
      }

      const assistantId = newId();
      appendBaseMessage({
        id: assistantId,
        role: "assistant",
        content: "",
        pending: true,
        status: "loading",
        message_type: "text",
        created_at: new Date().toISOString(),
      });

      setIsBusy(true);
      const controller = new AbortController();
      abortRef.current = controller;

      try {
        await chatService.stream({
          message: text,
          threadId: activeThreadId,
          attachments,
          signal: controller.signal,
          onThread: (threadId) => {
            if (threadId !== activeThreadId) {
              setActiveThreadId(threadId);
            }
          },
          onToken: (token) => {
            patchBaseMessage(assistantId, (prev) => ({
              ...prev,
              content: `${prev.content}${token}`,
            }));
          },
        });

        await refreshThreads();
      } catch (err) {
        const errorText = err instanceof Error ? err.message : "Something went wrong.";
        patchBaseMessage(assistantId, (prev) => ({
          ...prev,
          content: prev.content || `Error: ${errorText}`,
          status: "error",
          error: errorText,
        }));
      } finally {
        patchBaseMessage(assistantId, (prev) => ({
          ...prev,
          pending: false,
          status: prev.status === "error" ? "error" : "success",
        }));
        setIsBusy(false);
        abortRef.current = null;
      }
    },
    [
      activeThreadId,
      appendBaseMessage,
      handleImageGeneration,
      isBusy,
      newId,
      patchBaseMessage,
      ragDocuments,
      refreshThreads,
      setActiveThreadId,
    ]
  );

  return {
    isBusy,
    abortRef,
    handleSendMessage,
    handleImageGeneration,
    handlePdfUpload,
  };
}
