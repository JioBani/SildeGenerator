import path from "node:path";
import { config } from "../config/app-config";
import type { ImageModel } from "./image-model";
import type { ImageStyle } from "./image-style";
import type { MotionStyleSnapshot } from "./motion-style";
import type { SlideVisualProfile } from "./slide-visual-profile";
import type { MusicSelection } from "./music-selection";
import type { VoiceSettingsSnapshot } from "./voice-settings";
import type { HarnessSnapshot } from "./harness";
import type { VisualCue } from "./scenario-input";

export const RENDER_QUEUE = "video-jobs";

export type RenderJobData = {
  genreId?: import("./video-genre").VideoGenre;
  genreVersion?: string;
  scenario: string;
  visualCues?: VisualCue[];
  userId: string;
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
  narrationSpeed: number;
  harnessId: string;
  harnessSnapshot: HarnessSnapshot;
  durationProfile: import("./duration-policy").DurationProfile;
  aspectRatio: "16:9" | "9:16";
  subtitlesEnabled: boolean;
};
export type RenderJobProgress = { step: string; percent: number; sceneId?: string; message?: string };

export const jobPaths = (id: string) => {
  const root = path.join(config.dataDir, "jobs", id);
  return {
    root,
    input: path.join(root, "input"),
    scenario: path.join(root, "input", "scenario.md"),
    work: path.join(root, "work"),
    output: path.join(root, "output"),
    video: path.join(root, "output", "video.mp4"),
    progress: path.join(root, "progress.json"),
    logs: path.join(root, "logs"),
  };
};

export type JobPaths = ReturnType<typeof jobPaths>;
