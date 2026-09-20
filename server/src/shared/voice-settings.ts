export const VOICE_PROVIDERS = ["mock", "microsoft_edge", "elevenlabs"] as const;
export type VoiceProvider = typeof VOICE_PROVIDERS[number];
export const DEFAULT_NARRATION_SPEED = 0.7;
export const MIN_NARRATION_SPEED = 0.7;
export const MAX_NARRATION_SPEED = 1.2;

export type VoiceSettingsSnapshot = {
  provider: VoiceProvider;
  model: string;
  voiceId: string;
  voiceName: string;
  rate?: string;
  pitch?: string;
  volume?: string;
  stability?: number;
  similarityBoost?: number;
  speed?: number;
  version: number;
};

export function applyNarrationSpeed(snapshot: VoiceSettingsSnapshot, narrationSpeed: number): VoiceSettingsSnapshot {
  const speed = Math.min(MAX_NARRATION_SPEED, Math.max(MIN_NARRATION_SPEED, narrationSpeed));
  if (snapshot.provider === "microsoft_edge") {
    const percent = Math.round((speed - 1) * 100);
    return { ...snapshot, speed, rate: `${percent >= 0 ? "+" : ""}${percent}%` };
  }
  return { ...snapshot, speed };
}
