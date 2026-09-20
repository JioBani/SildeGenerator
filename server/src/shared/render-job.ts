import path from "node:path";
import { config } from "../config/app-config";
import type { ImageModel } from "./image-model";
import type { ImageStyle } from "./image-style";
import type { VoiceSettingsSnapshot } from "./voice-settings";
import type { HarnessSnapshot } from "./harness";

export const RENDER_QUEUE = "video-jobs";

export type RenderJobData = {
  scenario: string;
  userId: string;
  codexModel: string;
  codexReasoningEffort: "low" | "medium" | "high" | "xhigh" | "max";
  codexFastMode: boolean;
  imageModel: ImageModel;
  continuityEnabled: boolean;
  imageStyle: ImageStyle;
  voiceSettings: VoiceSettingsSnapshot;
  narrationSpeed: number;
  harnessId: string;
  harnessSnapshot: HarnessSnapshot;
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
