import type { ImageStyle } from "./image-style";

// Compatibility surface for stored jobs. User-facing genre selection was removed
// in favor of one motion-graphics format with per-scene directing strategies.
export const VIDEO_GENRES = ["motion_graphic"] as const;
export type VideoGenre = typeof VIDEO_GENRES[number];
export const GENRE_VERSION = "1.0.0";

export const GENRE_OPTIONS = [{
  id: "motion_graphic",
  name: "모션그래픽",
  description: "장면 기능에 따라 정보·오브젝트·움직임을 설계",
  defaultImageStyle: "graphic_explainer",
  signals: [],
  version: GENRE_VERSION,
  status: "internal_contract",
  productionAvailable: true,
  supportedHarnesses: ["astra-motion"],
  humanReviewRequired: true,
}] as const;

export function supportsGenreDraft(genreId: VideoGenre, harnessId: string): boolean {
  return genreId === "motion_graphic" && harnessId === "astra-motion";
}

export function defaultImageStyleForGenre(_genreId: VideoGenre): ImageStyle {
  return "graphic_explainer";
}
