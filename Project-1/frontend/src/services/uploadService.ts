import { uploadApi } from "../lib/endpoints";
import type { MessageAttachment } from "../types";

export const uploadService = {
  uploadFiles: async (files: File[]): Promise<MessageAttachment[]> => {
    console.debug("[uploadService] uploadFiles", { count: files.length });

    const uploaded: MessageAttachment[] = [];
    for (const file of files) {
      const result = await uploadApi.uploadFile(file);
      const metadata: Record<string, unknown> = {
        size_bytes: result.size_bytes,
      };

      if (result.video_frames && result.video_frames.length > 0) {
        metadata.video_frames = result.video_frames;
      }

      uploaded.push({
        attachment_type: result.attachment_type,
        attachment_url: result.attachment_url,
        content: result.content || undefined,
        name: result.name,
        mime_type: result.mime_type,
        metadata,
      });
    }

    return uploaded;
  },
};
