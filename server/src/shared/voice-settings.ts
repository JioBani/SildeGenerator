export const VOICE_PROVIDERS = ["mock", "microsoft_edge", "elevenlabs"] as const;
export type VoiceProvider = typeof VOICE_PROVIDERS[number];

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
  playbackSpeed?: number;
  version: number;
};
