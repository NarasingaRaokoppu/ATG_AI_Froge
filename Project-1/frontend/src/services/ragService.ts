import { ragApi } from "../lib/endpoints";

export const ragService = {
  uploadPdf: (threadId: string, file: File) => {
    console.debug("[ragService] uploadPdf", { threadId, name: file.name });
    return ragApi.uploadPdf(threadId, file);
  },
  chat: (payload: {
    thread_id: string;
    question: string;
    top_k?: number;
    document_ids?: string[];
  }) => {
    console.debug("[ragService] chat", {
      threadId: payload.thread_id,
      docs: payload.document_ids?.length ?? 0,
    });
    return ragApi.chat(payload);
  },
  listDocuments: (threadId: string) => ragApi.listDocuments(threadId),
  deleteDocument: (threadId: string, documentId: string) =>
    ragApi.deleteDocument(threadId, documentId),
};
