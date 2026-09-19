export const IMAGE_MODELS = [
  "gpt-image-2",
  "gpt-image-2.5-sunburst",
  "gpt-image-2.5-flare",
] as const;

export type ImageModel = typeof IMAGE_MODELS[number];
export const DEFAULT_IMAGE_MODEL: ImageModel = "gpt-image-2.5-sunburst";
