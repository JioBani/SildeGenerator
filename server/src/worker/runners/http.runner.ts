import { Injectable } from "@nestjs/common";
import { config } from "../../config/app-config";
import type { RunContext, RunnerResult, VideoRunner } from "./video-runner";
import { postJson } from "./http-json";

export function assertRunnerConfiguration(
  runtime: { mode?: string; imageProvider?: string },
  expected = { mode: config.runnerMode, imageProvider: config.imageProvider },
): void {
  if (runtime.mode !== expected.mode || runtime.imageProvider !== expected.imageProvider) {
    throw new Error(`영상 작업기 설정 불일치: 요청 ${expected.mode}/${expected.imageProvider}, 실행 ${runtime.mode ?? "unknown"}/${runtime.imageProvider ?? "unknown"}`);
  }
}

@Injectable()
export class HttpRunner implements VideoRunner {
  async run({ jobId, attempt, scenario, visualCues, signal, codexModel, codexReasoningEffort, codexFastMode, imageModel, continuityEnabled, imageStyle, motionStyle, slideVisualProfile, musicSelection, voiceSettings, harnessId, harnessSnapshot, durationProfile, aspectRatio, subtitlesEnabled, genreId, genreVersion }: RunContext): Promise<RunnerResult> {
    const health = await fetch(`${config.runnerUrl}/health`, { signal });
    if (!health.ok) throw new Error(`영상 작업기 상태 확인 실패: HTTP ${health.status}`);
    assertRunnerConfiguration(await health.json() as { mode?: string; imageProvider?: string });
    const response = await postJson(`${config.runnerUrl}/render`, {
        production_job: true,
        job_id: jobId,
        attempt,
        scenario,
        visual_cues: visualCues ?? [],
        codex_model: codexModel,
        codex_reasoning_effort: codexReasoningEffort,
        codex_fast_mode: codexFastMode,
        image_model: imageModel,
        continuity_enabled: continuityEnabled,
        image_style: imageStyle,
        motion_style: motionStyle,
        slide_visual_profile: slideVisualProfile,
        music_selection: musicSelection,
        genre_id: genreId,
        genre_version: genreVersion,
        voice_settings: {
          provider: voiceSettings.provider, model: voiceSettings.model,
          voice_id: voiceSettings.voiceId, voice_name: voiceSettings.voiceName,
          rate: voiceSettings.rate, pitch: voiceSettings.pitch, volume: voiceSettings.volume,
          stability: voiceSettings.stability, similarity_boost: voiceSettings.similarityBoost,
          speed: voiceSettings.speed, version: voiceSettings.version,
        },
        harness_id: harnessId,
        harness_snapshot: harnessSnapshot,
        duration_profile: durationProfile,
        aspect_ratio: aspectRatio,
        subtitles_enabled: subtitlesEnabled,
      }, signal, { "X-Slidegen-Job": jobId });
    let payload: unknown;
    try { payload = JSON.parse(response.text); } catch { throw new Error(`runner returned invalid JSON (${response.status})`); }
    if (response.status < 200 || response.status >= 300) {
      const rawDetail = typeof payload === "object" && payload && "detail" in payload
        ? (payload as { detail: unknown }).detail
        : `HTTP ${response.status}`;
      const detail = typeof rawDetail === "string" ? rawDetail : JSON.stringify(rawDetail);
      throw new Error(`runner failed: ${detail}`);
    }
    return payload as RunnerResult;
  }
}
