export const KOREAN_NARRATION_CHARS_PER_SECOND = 5.7;

export type DurationEstimate = {
  normalizedCharacters: number;
  centerSeconds: number;
  minSeconds: number;
  maxSeconds: number;
};

const roundRange = (seconds: number) => Math.max(1, Math.round(seconds / 5) * 5);

export function estimateNarrationDuration(scenario: string): DurationEstimate | null {
  const normalized = scenario.trim().replace(/\s+/g, " ");
  if (!normalized) return null;
  const center = normalized.length / KOREAN_NARRATION_CHARS_PER_SECOND;
  return {
    normalizedCharacters: normalized.length,
    centerSeconds: roundRange(center),
    minSeconds: roundRange(center * 0.88),
    maxSeconds: roundRange(center * 1.12),
  };
}

export function formatPlaybackDuration(seconds: number) {
  const rounded = Math.max(1, Math.round(seconds));
  if (rounded >= 3600) return `${Math.floor(rounded / 3600)}시간 ${Math.floor((rounded % 3600) / 60)}분`;
  if (rounded >= 60) return `${Math.floor(rounded / 60)}분 ${rounded % 60}초`;
  return `${rounded}초`;
}
