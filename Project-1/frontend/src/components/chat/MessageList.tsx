import { useEffect, useRef } from "react";

import type { ChatMessage } from "../../types";
import { MessageBubble } from "./MessageBubble";

interface MessageListProps {
  messages: ChatMessage[];
  isStreaming?: boolean;
}

export function MessageList({ messages, isStreaming = false }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center px-4">
        <div className="max-w-md rounded-2xl border border-gray-200 bg-white p-8 text-center shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100 sm:text-2xl">
            Start a new conversation
          </h2>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            Ask anything. I will remember recent turns in this thread for better
            context-aware responses.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto py-3 sm:py-4">
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} />
      ))}
      {isStreaming && (
        <div className="px-4 pb-2 text-xs text-gray-500 dark:text-gray-400">
          Assistant is typing...
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
