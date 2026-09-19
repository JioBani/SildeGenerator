export const IMAGE_STYLES = ["editorial_illustration", "cinematic_realism", "graphic_explainer"] as const;
export type ImageStyle = typeof IMAGE_STYLES[number];
export const DEFAULT_IMAGE_STYLE: ImageStyle = "editorial_illustration";
