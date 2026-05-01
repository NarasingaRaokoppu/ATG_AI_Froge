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
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const justCreatedRef = useRef(false);

  // Initial thread load
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await threadApi.list();
        if (cancelled) return;
        setThreads(list);
        if (list.length > 0) setActiveThreadId(list[0].id);
      } finally {
        if (!cancelled) setThreadsLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

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
  }, [isStreaming]);

  const handleSelect = useCallback(
    (id: string | null) => {
      if (isStreaming) return;
      setActiveThreadId(id);
    },
    [isStreaming]
  );

  const handleDelete = useCallback(
    async (id: string) => {
      await threadApi.remove(id);
      setThreads((prev) => prev.filter((t) => t.id !== id));
      if (activeThreadId === id) {
        setActiveThreadId(null);
        setMessages([]);
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

      let createdThreadId: string | null = null;

      try {
        await streamChat({
          message: text,
          threadId: activeThreadId,
          signal: controller.signal,
          onThread: (threadId) => {
            if (threadId !== activeThreadId) {
              createdThreadId = threadId;
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

        // Refresh sidebar so the new thread + auto-title appear
        if (createdThreadId || !activeThreadId) {
          const list = await threadApi.list();
          setThreads(list);
        } else {
          // title may have just been set on first message
          const list = await threadApi.list();
          setThreads(list);
        }
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
    [activeThreadId, isStreaming]
  );

  return (
    <div className="flex h-screen bg-white dark:bg-gray-950">
      <Sidebar
        threads={threads}
        activeThreadId={activeThreadId}
        onSelect={handleSelect}
        onNewChat={handleNewChat}
        onDelete={handleDelete}
        onRename={handleRename}
        loading={threadsLoading}
      />

      <div className="flex flex-1 flex-col">
        <header className="border-b border-gray-200 bg-white px-6 py-4 dark:border-gray-800 dark:bg-gray-900">
          <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Amzur AI Chat
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Gemini · via LiteLLM proxy
          </p>
        </header>

        <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col overflow-hidden">
          <MessageList messages={messages} />
        </main>

        <InputBar disabled={isStreaming} onSend={sendMessage} />
      </div>
    </div>
  );
}
