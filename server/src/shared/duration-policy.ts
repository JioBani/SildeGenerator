export type DurationProfile = "episode_60" | "single_30m";

const narrationCharactersPerSecond = 5.7;

export function durationProfileForHarness(harnessId: string): DurationProfile {
  return harnessId === "classic-slide" || harnessId === "cinematic-slide" ? "single_30m" : "episode_60";
}

export function estimatedNarrationSeconds(scenario: string, speed: number, voiceProvider?: string): number {
  const characters = scenario.trim().replace(/\s+/g, " ").length;
  // Measured Korean Edge narration was slower than the legacy generic estimate.
  // Keep a margin because pauses and punctuation differ between scripts.
  if (voiceProvider === "microsoft_edge") return characters / (6.3 * speed);
  return characters / narrationCharactersPerSecond / (speed / 0.7);
}

export function maximumSeconds(profile: DurationProfile): number {
  return profile === "single_30m" ? 1800 : 60;
}
