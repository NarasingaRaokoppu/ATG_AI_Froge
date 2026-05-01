import ReactMarkdown from "react-markdown";

import { AttachmentPreview } from "../attachments/AttachmentPreview";
import type { ChatMessage } from "../../types";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex w-full ${isUser ? "justify-end" : "justify-start"} px-4 py-2`}
    >
      <div
        className={`max-w-2xl rounded-2xl px-4 py-3 text-justify shadow-sm ${
          isUser
            ? "bg-blue-600 text-white rounded-br-sm"
            : "bg-gray-100 text-gray-900 rounded-bl-sm dark:bg-gray-800 dark:text-gray-100"
        }`}
      >
        {message.content ? (
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        ) : (
          <TypingIndicator />
        )}

        {message.attachments && message.attachments.length > 0 ? (
          <div className="mt-3">
            <AttachmentPreview attachments={message.attachments} />
          </div>
        ) : null}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 py-1">
      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.3s]" />
      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.15s]" />
      <span className="h-2 w-2 animate-bounce rounded-full bg-gray-400" />
    </div>
  );
}
