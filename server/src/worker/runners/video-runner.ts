import type { JobPaths } from "../../shared/render-job";
import type { RunnerAsset, RunnerStage, RunnerUsage } from "../../metrics/metrics.service";
import type { ImageModel } from "../../shared/image-model";
import type { ImageStyle } from "../../shared/image-style";
import type { VoiceSettingsSnapshot } from "../../shared/voice-settings";
import type { HarnessSnapshot } from "../../shared/harness";

export const VIDEO_RUNNER = Symbol("VIDEO_RUNNER");

export type RunContext = {
  jobId: string;
  attempt: number;
  scenario: string;
  paths: JobPaths;
  signal: AbortSignal;
  codexModel: string;
  codexReasoningEffort: "low" | "medium" | "high" | "xhigh" | "max";
  codexFastMode: boolean;
  imageModel: ImageModel;
  continuityEnabled: boolean;
  imageStyle: ImageStyle;
  voiceSettings: VoiceSettingsSnapshot;
  harnessId: string;
  harnessSnapshot: HarnessSnapshot;
};

export type RunnerResult = {
  success: boolean;
  video_path: string;
  message: string;
  stages: RunnerStage[];
  usage: RunnerUsage[];
  assets: RunnerAsset[];
  prompts: Array<{ name: string; relative_path: string; sha256: string; content: string }>;
  narrative_blueprint?: Record<string, unknown> | null;
  harness_snapshot?: HarnessSnapshot | null;
};

export interface VideoRunner {
  run(ctx: RunContext): Promise<RunnerResult>;
}
