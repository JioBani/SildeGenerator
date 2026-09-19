export type VoiceProvider = "mock" | "microsoft_edge" | "elevenlabs";
export type VoiceDraft = {
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
};
export type ProviderMemory = Partial<Record<VoiceProvider, Omit<VoiceDraft, "provider">>>;

const defaults: Record<VoiceProvider, Omit<VoiceDraft, "provider">> = {
  mock: { model: "mock-silence-v1", voiceId: "mock", voiceName: "Mock silence" },
  microsoft_edge: { model: "edge-tts", voiceId: "ko-KR-InJoonNeural", voiceName: "인준", rate: "-30%", pitch: "+0Hz", volume: "+0%" },
  elevenlabs: { model: "eleven_flash_v2_5", voiceId: "nPczCjzI2devNBz1zQrb", voiceName: "Brian", stability: 0.6, similarityBoost: 0.6, speed: 0.7 },
};

function fields(draft: VoiceDraft): Omit<VoiceDraft, "provider"> {
  const { provider: _provider, ...providerFields } = draft;
  return providerFields;
}

export function switchVoiceProvider(draft: VoiceDraft, target: VoiceProvider, memory: ProviderMemory, saved?: VoiceDraft | null) {
  const nextMemory: ProviderMemory = { ...memory, [draft.provider]: fields(draft) };
  const restored = nextMemory[target] ?? (saved?.provider === target ? fields(saved) : defaults[target]);
  return { draft: { ...draft, ...restored, provider: target }, memory: nextMemory };
}
