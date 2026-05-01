import { useCallback, useEffect, useRef, useState } from "react";

import { messageApi, threadApi } from "../../lib/endpoints";
import { streamChat } from "../../lib/chatStream";
import type { ChatMessage, Thread } from "../../types";
import { InputBar } from "./InputBar";
import { MessageList } from "./MessageList";
import { Sidebar } from "./Sidebar";

const newId = () =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2);

export function ChatContainer() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [threadsLoading, setThreadsLoading] = useState(true);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const justCreatedRef = useRef(false);

  const refreshThreads = useCallback(async () => {
    const list = await threadApi.list();
    setThreads(list);
    return list;
  }, []);

  // Initial thread load
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

  // Load messages whenever the active thread changes
  useEffect(() => {
    if (!activeThreadId) {
      setMessages([]);
      return;
    }
    if (justCreatedRef.current) {
      // Thread was just created in-flight; do not wipe streaming state.
      justCreatedRef.current = false;
      return;
    }
    let cancelled = false;
    (async () => {
      const dtos = await messageApi.list(activeThreadId);
      if (cancelled) return;
      setMessages(
        dtos.map((m) => ({ id: m.id, role: m.role, content: m.content }))
      );
    })();
    return () => {
      cancelled = true;
    };
  }, [activeThreadId]);

  const handleNewChat = useCallback(() => {
    if (isStreaming) return;
    setActiveThreadId(null);
    setMessages([]);
    setSidebarOpen(false);
  }, [isStreaming]);

  const handleSelect = useCallback(
    (id: string | null) => {
      if (isStreaming) return;
      setActiveThreadId(id);
      setSidebarOpen(false);
    },
    [isStreaming]
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
        const fallback = nextThreads[0]?.id ?? null;
        setActiveThreadId(fallback);
        if (!fallback) setMessages([]);
      }
    },
    [activeThreadId]
  );

  const handleRename = useCallback(async (id: string, title: string) => {
    const updated = await threadApi.rename(id, title);
    setThreads((prev) => prev.map((t) => (t.id === id ? updated : t)));
  }, []);

  const sendMessage = useCallback(
    async (text: string) => {
      if (isStreaming) return;

      const userMsg: ChatMessage = {
        id: newId(),
        role: "user",
        content: text,
      };
      const assistantId = newId();
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        pending: true,
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsStreaming(true);

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        await streamChat({
          message: text,
          threadId: activeThreadId,
          signal: controller.signal,
          onThread: (threadId) => {
            if (threadId !== activeThreadId) {
              justCreatedRef.current = true;
              setActiveThreadId(threadId);
            }
          },
          onToken: (token) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: m.content + token }
                  : m
              )
            );
          },
        });

        // Refresh sidebar so new threads and latest auto-title are reflected.
        await refreshThreads();
      } catch (err) {
        const errorText =
          err instanceof Error ? err.message : "Something went wrong.";
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content: m.content || `**Error:** ${errorText}`,
                }
              : m
          )
        );
      } finally {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, pending: false } : m
          )
        );
        setIsStreaming(false);
        abortRef.current = null;
      }
    },
    [activeThreadId, isStreaming, refreshThreads]
  );

  const activeThread = threads.find((t) => t.id === activeThreadId) ?? null;

  return (
    <div className="flex h-dvh bg-white dark:bg-gray-950">
      {sidebarOpen && (
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
      )}

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
        <header className="border-b border-gray-200 bg-white px-4 py-3 dark:border-gray-800 dark:bg-gray-900 sm:px-6 sm:py-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setSidebarOpen(true)}
              className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-gray-300 text-gray-700 hover:bg-gray-100 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800 lg:hidden"
              aria-label="Open threads"
            >
              ≡
            </button>

            <div>
              <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Amzur AI Chat
              </h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {activeThread?.title || "New conversation"}
              </p>
            </div>
          </div>

          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Amzur AI Chat
            Gemini · via LiteLLM proxy
          </p>
        </header>

        <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col overflow-hidden px-2 sm:px-4">
          <MessageList messages={messages} isStreaming={isStreaming} />
        </main>

        <InputBar disabled={isStreaming} onSend={sendMessage} />
      </div>
    </div>
  );
}
