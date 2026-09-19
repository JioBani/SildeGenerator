import { BadRequestException, Injectable } from "@nestjs/common";
import { config } from "../config/app-config";
import { DatabaseService } from "../database/database.service";
import { VOICE_PROVIDERS, type VoiceProvider, type VoiceSettingsSnapshot } from "../shared/voice-settings";

export type VoiceRuntimeSettings = Omit<VoiceSettingsSnapshot, "version">;

@Injectable()
export class VoiceSettingsService {
  constructor(private readonly db: DatabaseService) {}

  private defaults(): VoiceRuntimeSettings {
    const provider = VOICE_PROVIDERS.includes(config.voiceProvider as VoiceProvider) ? config.voiceProvider as VoiceProvider : "mock";
    if (provider === "microsoft_edge") return { provider, model: "edge-tts", voiceId: config.microsoftEdgeVoice, voiceName: config.microsoftEdgeVoice, rate: config.microsoftEdgeRate, pitch: config.microsoftEdgePitch, volume: config.microsoftEdgeVolume };
    if (provider === "elevenlabs") return { provider, model: config.elevenLabsModel, voiceId: config.elevenLabsVoiceId, voiceName: config.elevenLabsVoiceName, stability: config.elevenLabsStability, similarityBoost: config.elevenLabsSimilarityBoost, speed: config.elevenLabsSpeed };
    return { provider: "mock", model: "mock-silence-v1", voiceId: "mock", voiceName: "무음 Mock" };
  }

  async get() {
    const result = await this.db.query<{ value: Partial<VoiceRuntimeSettings>; updated_at: Date }>(`SELECT value,updated_at FROM runtime_settings WHERE key='voice_generation'`);
    const value = this.validate({ ...this.defaults(), ...(result.rows[0]?.value ?? {}) });
    return { ...value, providerOptions: VOICE_PROVIDERS, elevenLabsConfigured: config.elevenLabsConfigured, updatedAt: result.rows[0]?.updated_at ?? null };
  }

  async snapshot(): Promise<VoiceSettingsSnapshot> {
    const current = await this.get();
    return { provider: current.provider, model: current.model, voiceId: current.voiceId, voiceName: current.voiceName, rate: current.rate, pitch: current.pitch, volume: current.volume, stability: current.stability, similarityBoost: current.similarityBoost, speed: current.speed, version: current.updatedAt ? new Date(current.updatedAt).getTime() : 1 };
  }

  async update(value: Partial<VoiceRuntimeSettings>) {
    const validated = this.validate(value);
    const result = await this.db.query<{ updated_at: Date }>(`INSERT INTO runtime_settings(key,value,updated_at) VALUES('voice_generation',$1,now()) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=now() RETURNING updated_at`, [validated]);
    return { ...validated, providerOptions: VOICE_PROVIDERS, elevenLabsConfigured: config.elevenLabsConfigured, updatedAt: result.rows[0].updated_at };
  }

  private validate(value: Partial<VoiceRuntimeSettings>): VoiceRuntimeSettings {
    if (!value.provider || !VOICE_PROVIDERS.includes(value.provider as VoiceProvider)) throw new BadRequestException("지원하는 음성 공급자를 선택해 주세요.");
    const provider = value.provider as VoiceProvider;
    if (provider === "mock") return { provider, model: "mock-silence-v1", voiceId: "mock", voiceName: "무음 Mock" };
    if (provider === "microsoft_edge") {
      const voiceId = String(value.voiceId ?? config.microsoftEdgeVoice);
      const rate = String(value.rate ?? config.microsoftEdgeRate);
      const pitch = String(value.pitch ?? config.microsoftEdgePitch);
      const volume = String(value.volume ?? config.microsoftEdgeVolume);
      if (!/^ko-KR-[A-Za-z]+Neural$/.test(voiceId)) throw new BadRequestException("한국어 Microsoft Edge voice를 선택해 주세요.");
      if (!/^[+-](?:100|[0-9]{1,2})%$/.test(rate)) throw new BadRequestException("말하기 속도는 -100%부터 +100% 형식이어야 합니다.");
      if (!/^[+-](?:100|[0-9]{1,2})Hz$/.test(pitch)) throw new BadRequestException("pitch는 -100Hz부터 +100Hz 형식이어야 합니다.");
      if (!/^[+-](?:100|[0-9]{1,2})%$/.test(volume)) throw new BadRequestException("volume은 -100%부터 +100% 형식이어야 합니다.");
      return { provider, model: "edge-tts", voiceId, voiceName: value.voiceName || voiceId, rate, pitch, volume };
    }
    const stability = Number(value.stability ?? config.elevenLabsStability);
    const similarityBoost = Number(value.similarityBoost ?? config.elevenLabsSimilarityBoost);
    const speed = Number(value.speed ?? config.elevenLabsSpeed);
    if (!config.elevenLabsConfigured) throw new BadRequestException("ElevenLabs API key가 설정되지 않았습니다.");
    if (![stability, similarityBoost].every((number) => number >= 0 && number <= 1) || speed < 0.7 || speed > 1.2) throw new BadRequestException("ElevenLabs 음성 설정 범위를 확인해 주세요.");
    return { provider, model: value.model || config.elevenLabsModel, voiceId: value.voiceId || config.elevenLabsVoiceId, voiceName: value.voiceName || config.elevenLabsVoiceName, stability, similarityBoost, speed };
  }
}
