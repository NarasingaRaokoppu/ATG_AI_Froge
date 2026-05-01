import { useEffect, useRef } from "react";

import type { ChatMessage } from "../../types";
import { MessageBubble } from "./MessageBubble";

interface MessageListProps {
  messages: ChatMessage[];
}

export function MessageList({ messages }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center px-4">
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-gray-700 dark:text-gray-200">
            How can I help you today?
          </h2>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            Ask anything — I&apos;m powered by Gemini via the Amzur LiteLLM
            proxy.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto py-4">
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
