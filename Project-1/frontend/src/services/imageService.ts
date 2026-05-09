import { imageApi } from "../lib/endpoints";
import type { ImageAspectRatio, ImageStyle } from "../types";

export const imageService = {
  generate: (payload: {
    prompt: string;
    thread_id: string | null;
    style: ImageStyle;
    aspect_ratio: ImageAspectRatio;
    enhance_prompt: boolean;
  }) => {
    console.debug("[imageService] generate", {
      threadId: payload.thread_id,
      style: payload.style,
      aspect: payload.aspect_ratio,
    });
    return imageApi.generate(payload);
  },
  regenerate: (payload: {
    image_id: string;
    prompt_override?: string | null;
    style?: ImageStyle;
    aspect_ratio?: ImageAspectRatio;
    enhance_prompt?: boolean;
  }) => imageApi.regenerate(payload),
  listByThread: (threadId: string) => imageApi.listByThread(threadId),
  remove: (imageId: string) => imageApi.remove(imageId),
};
