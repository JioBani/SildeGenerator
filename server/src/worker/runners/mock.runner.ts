import { execFile } from "node:child_process";
import { writeFile } from "node:fs/promises";
import { promisify } from "node:util";
import { Injectable } from "@nestjs/common";
import type { RunContext, RunnerResult, VideoRunner } from "./video-runner";
import { config } from "../../config/app-config";

const exec = promisify(execFile);

// codex 없이 배포 파이프라인(큐 → 워커 → 파일 → 다운로드)을 점검하기 위한 러너
@Injectable()
export class MockRunner implements VideoRunner {
  async run({ paths, signal }: RunContext): Promise<RunnerResult> {
    await writeFile(paths.progress, JSON.stringify({ step: "mock render", percent: 50 }));
    await exec(
      "ffmpeg",
      ["-y", "-f", "lavfi", "-i", `testsrc=size=1280x720:rate=${config.videoFps}`, "-f", "lavfi", "-i", "sine=frequency=440",
       "-t", "5", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", paths.video],
      { signal },
    );
    return { success: true, video_path: paths.video, message: "mock", stages: [], usage: [], assets: [], prompts: [] };
  }
}
