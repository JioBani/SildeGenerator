import type { JobPaths } from "../../shared/render-job";
import type { RunnerAsset, RunnerStage, RunnerUsage } from "../../metrics/metrics.service";
import type { ImageModel } from "../../shared/image-model";
import type { ImageStyle } from "../../shared/image-style";
import type { MotionStyleSnapshot } from "../../shared/motion-style";
import type { SlideVisualProfile } from "../../shared/slide-visual-profile";
import type { MusicSelection } from "../../shared/music-selection";
import type { VoiceSettingsSnapshot } from "../../shared/voice-settings";
import type { HarnessSnapshot } from "../../shared/harness";
import type { VisualCue } from "../../shared/scenario-input";

export const VIDEO_RUNNER = Symbol("VIDEO_RUNNER");

export type RunContext = {
  genreId?: import("../../shared/video-genre").VideoGenre;
  genreVersion?: string;
  jobId: string;
  attempt: number;
  scenario: string;
  visualCues?: VisualCue[];
  paths: JobPaths;
  signal: AbortSignal;
  codexModel: string;
  codexReasoningEffort: "low" | "medium" | "high" | "xhigh" | "max";
  codexFastMode: boolean;
  imageModel: ImageModel;
  continuityEnabled: boolean;
  imageStyle: ImageStyle;
  motionStyle: MotionStyleSnapshot | null;
  slideVisualProfile: SlideVisualProfile | null;
  musicSelection: MusicSelection;
  voiceSettings: VoiceSettingsSnapshot;
  harnessId: string;
  harnessSnapshot: HarnessSnapshot;
  durationProfile: import("../../shared/duration-policy").DurationProfile;
  aspectRatio: "16:9" | "9:16";
  subtitlesEnabled: boolean;
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
  production_pack?: Record<string, unknown> | null;
  quality_gate_report?: Record<string, unknown> | null;
};

export interface VideoRunner {
  run(ctx: RunContext): Promise<RunnerResult>;
}
