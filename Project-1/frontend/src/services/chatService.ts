import { streamChat } from "../lib/chatStream";
import type { MessageAttachment } from "../types";

export interface StreamChatParams {
  message: string;
  threadId: string | null;
  attachments?: MessageAttachment[];
  signal?: AbortSignal;
  onThread: (threadId: string) => void;
  onToken: (token: string) => void;
}

export const chatService = {
  stream: (params: StreamChatParams) => {
    console.debug("[chatService] stream dispatch", {
      threadId: params.threadId,
      attachments: params.attachments?.length ?? 0,
    });
    return streamChat(params);
  },
};
