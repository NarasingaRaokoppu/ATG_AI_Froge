import { useCallback, useEffect, useState } from "react";

import { threadApi } from "../../lib/endpoints";
import type { Thread } from "../../types";
import { useChatActions } from "../../hooks/useChatActions";
import { useThreadMessages } from "../../hooks/useThreadMessages";
import { InputBar } from "./InputBar";
import { ChatHeader } from "./ChatHeader";
import { EmptyState } from "./EmptyState";
import { MessageList } from "./MessageList";
import { Sidebar } from "./Sidebar";

export function ChatContainer() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [threadsLoading, setThreadsLoading] = useState(true);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const refreshThreads = useCallback(async () => {
    const list = await threadApi.list();
    setThreads(list);
    return list;
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await refreshThreads();
        if (cancelled) return;
        if (list.length > 0) setActiveThreadId(list[0].id);
      } finally {
        if (!cancelled) setThreadsLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [refreshThreads]);

  const {
    timelineMessages,
    ragDocuments,
    refreshGeneratedImages,
    refreshRagDocuments,
    appendBaseMessage,
    patchBaseMessage,
    newId,
  } = useThreadMessages(activeThreadId);

  const { isBusy, handleSendMessage, handleImageGeneration, handlePdfUpload } =
    useChatActions({
      activeThreadId,
      ragDocuments,
      setActiveThreadId,
      refreshThreads,
      refreshGeneratedImages,
      refreshRagDocuments,
      appendBaseMessage,
      patchBaseMessage,
      newId,
    });

  const handleNewChat = useCallback(() => {
    if (isBusy) return;
    setActiveThreadId(null);
    setSidebarOpen(false);
  }, [isBusy]);

  const handleSelect = useCallback(
    (id: string | null) => {
      if (isBusy) return;
      console.debug("[ChatContainer] thread switch", {
        from: activeThreadId,
        to: id,
      });
      setActiveThreadId(id);
      setSidebarOpen(false);
    },
    [activeThreadId, isBusy]
  );

  const handleDelete = useCallback(
    async (id: string) => {
      await threadApi.remove(id);
      let nextThreads: Thread[] = [];
      setThreads((prev) => {
        nextThreads = prev.filter((t) => t.id !== id);
        return nextThreads;
      });

      if (activeThreadId === id) {
        setActiveThreadId(nextThreads[0]?.id ?? null);
      }
    },
    [activeThreadId]
  );

  const handleRename = useCallback(async (id: string, title: string) => {
    const updated = await threadApi.rename(id, title);
    setThreads((prev) => prev.map((t) => (t.id === id ? updated : t)));
  }, []);

  const activeThread = threads.find((t) => t.id === activeThreadId) ?? null;

  return (
    <div className="flex h-dvh bg-white dark:bg-gray-950">
      {sidebarOpen ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            aria-label="Close sidebar"
            className="absolute inset-0 bg-black/40"
            onClick={() => setSidebarOpen(false)}
          />
          <div className="absolute left-0 top-0 h-full w-[82vw] max-w-xs">
            <Sidebar
              threads={threads}
              activeThreadId={activeThreadId}
              onSelect={handleSelect}
              onNewChat={handleNewChat}
              onDelete={handleDelete}
              onRename={handleRename}
              loading={threadsLoading}
            />
          </div>
        </div>
      ) : null}

      <div className="hidden lg:flex">
        <Sidebar
          threads={threads}
          activeThreadId={activeThreadId}
          onSelect={handleSelect}
          onNewChat={handleNewChat}
          onDelete={handleDelete}
          onRename={handleRename}
          loading={threadsLoading}
        />
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <ChatHeader
          activeThread={activeThread}
          sidebarOpen={sidebarOpen}
          onSidebarToggle={() => setSidebarOpen((o) => !o)}
        />

        <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col overflow-hidden px-2 sm:px-4">
          {timelineMessages.length === 0 ? (
            <EmptyState />
          ) : (
            <MessageList
              messages={timelineMessages}
              isStreaming={isBusy}
              onImageRegenerate={(image) => {
                void handleImageGeneration({
                  prompt: image.prompt,
                  style: (image.style as any) ?? undefined,
                  aspect_ratio: (image.aspect_ratio as any) ?? undefined,
                });
              }}
            />
          )}
        </main>

        <InputBar
          disabled={isBusy}
          activeThreadId={activeThreadId}
          onSend={handleSendMessage}
          onGenerateImage={handleImageGeneration}
          onUploadPdf={handlePdfUpload}
        />
      </div>
    </div>
  );
}
