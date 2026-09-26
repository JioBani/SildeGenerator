export const IMAGE_STYLES = ["editorial_illustration", "cinematic_realism", "graphic_explainer", "cute_character", "fantasy_anime", "animation_3d", "disney_animation", "dystopian"] as const;
export type ImageStyle = typeof IMAGE_STYLES[number];
export const DEFAULT_IMAGE_STYLE: ImageStyle = "editorial_illustration";
