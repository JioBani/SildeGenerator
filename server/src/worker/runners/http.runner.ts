import { Injectable } from "@nestjs/common";
import { config } from "../../config/app-config";
import type { RunContext, RunnerResult, VideoRunner } from "./video-runner";
import { postJson } from "./http-json";

@Injectable()
export class HttpRunner implements VideoRunner {
  async run({ jobId, attempt, scenario, signal, codexModel, codexReasoningEffort, codexFastMode, imageModel, continuityEnabled, imageStyle, voiceSettings, harnessId, harnessSnapshot }: RunContext): Promise<RunnerResult> {
    const response = await postJson(`${config.runnerUrl}/render`, {
        job_id: jobId,
        attempt,
        scenario,
        codex_model: codexModel,
        codex_reasoning_effort: codexReasoningEffort,
        codex_fast_mode: codexFastMode,
        image_model: imageModel,
        continuity_enabled: continuityEnabled,
        image_style: imageStyle,
        voice_settings: {
          provider: voiceSettings.provider, model: voiceSettings.model,
          voice_id: voiceSettings.voiceId, voice_name: voiceSettings.voiceName,
          rate: voiceSettings.rate, pitch: voiceSettings.pitch, volume: voiceSettings.volume,
          stability: voiceSettings.stability, similarity_boost: voiceSettings.similarityBoost,
          speed: voiceSettings.speed, playback_speed: voiceSettings.playbackSpeed, version: voiceSettings.version,
        },
        harness_id: harnessId,
        harness_snapshot: harnessSnapshot,
      }, signal, { "X-Slidegen-Job": jobId });
    let payload: unknown;
    try { payload = JSON.parse(response.text); } catch { throw new Error(`runner returned invalid JSON (${response.status})`); }
    if (response.status < 200 || response.status >= 300) {
      const detail = typeof payload === "object" && payload && "detail" in payload ? String((payload as { detail: unknown }).detail) : `HTTP ${response.status}`;
      throw new Error(`runner failed: ${detail}`);
    }
    return payload as RunnerResult;
  }
}
