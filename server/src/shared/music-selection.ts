export type MusicSelection =
  | { mode: "none" }
  | { mode: "auto"; preset: "warm-story" | "fantasy-night" | "quiet-reflection" }
  | { mode: "upload"; uploadId: string; path: string; sha256: string; mimeType: string };

export function publicMusicSelection(selection: MusicSelection | null | undefined) {
  if (!selection || selection.mode === "none") return { mode: "none" };
  if (selection.mode === "auto") return { mode: "auto", preset: selection.preset };
  return { mode: "upload", uploadId: selection.uploadId };
}

export function autoMusicPreset(scenario: string, style: string): "warm-story" | "fantasy-night" | "quiet-reflection" {
  if (["기도", "묵상", "눈물", "이별", "슬픔", "평안", "고요", "새벽"].some((word) => scenario.includes(word))) {
    return "quiet-reflection";
  }
  return style === "fantasy_anime" ? "fantasy-night" : "warm-story";
}
