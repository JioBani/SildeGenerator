import type { ImageStyle } from "./image-style";

export const SLIDE_VISUAL_PROFILE_VERSION = "0.5.0";

export type SlideVisualProfile = {
  id: "local_illustration";
  version: typeof SLIDE_VISUAL_PROFILE_VERSION;
  imageStyle: "cute_character" | "fantasy_anime";
};

export function slideVisualProfile(style: ImageStyle): SlideVisualProfile {
  if (style !== "cute_character" && style !== "fantasy_anime") {
    throw new Error("Local illustration supports the two illustrated slide styles only");
  }
  return { id: "local_illustration", version: SLIDE_VISUAL_PROFILE_VERSION, imageStyle: style };
}
