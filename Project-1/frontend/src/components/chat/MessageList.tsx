import { useEffect, useRef } from "react";

import { MessageBubble } from "./MessageBubble";
import type { ChatMessage, GeneratedImage } from "../../types";

interface MessageListProps {
  messages: ChatMessage[];
  isStreaming?: boolean;
  onImageRegenerate?: (image: GeneratedImage) => void;
}

export function MessageList({
  messages,
  isStreaming = false,
  onImageRegenerate,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    console.debug("[MessageList] final message list before render", {
      count: messages.length,
      imageCount: messages.filter((m) => m.message_type === "image").length,
      ids: messages.slice(-10).map((m) => m.id),
    });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto py-3 sm:py-4">
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} onImageRegenerate={onImageRegenerate} />
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
