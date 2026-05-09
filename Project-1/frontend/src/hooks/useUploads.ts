import { useCallback, useState } from "react";

import { APIError } from "../lib/api";
import { uploadService } from "../services/uploadService";

const MAX_FILE_MB = 20;
const MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024;

export function useUploads() {
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const uploadAttachments = useCallback(async (files: File[]) => {
    setUploadError(null);

    for (const file of files) {
      if (file.size > MAX_FILE_BYTES) {
        throw new Error(`"${file.name}" exceeds the ${MAX_FILE_MB}MB file size limit.`);
      }
    }

    setUploading(true);
    try {
      const uploaded = await uploadService.uploadFiles(files);
      return uploaded;
    } catch (error) {
      if (error instanceof APIError) {
        const detail =
          typeof error.detail === "string"
            ? error.detail
            : JSON.stringify(error.detail);
        const text = `Upload failed: ${detail}`;
        setUploadError(text);
        throw new Error(text);
      }

      const text = error instanceof Error ? error.message : "Upload failed. Please try again.";
      setUploadError(text);
      throw new Error(text);
    } finally {
      setUploading(false);
    }
  }, []);

  return {
    uploading,
    uploadError,
    uploadAttachments,
    setUploadError,
    setUploading,
  };
}
