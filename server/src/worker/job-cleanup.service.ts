import { readdir, rm, stat } from "node:fs/promises";
import path from "node:path";
import { Injectable, OnModuleDestroy, OnModuleInit } from "@nestjs/common";
import { config } from "../config/app-config";

// 보관 기간이 지난 작업 폴더 삭제
@Injectable()
export class JobCleanupService implements OnModuleInit, OnModuleDestroy {
  private timer?: NodeJS.Timeout;

  onModuleInit() {
    void this.cleanup();
    this.timer = setInterval(() => void this.cleanup(), 3_600_000);
  }

  onModuleDestroy() {
    clearInterval(this.timer);
  }

  private async cleanup() {
    const dir = path.join(config.dataDir, "jobs");
    const entries = await readdir(dir).catch(() => [] as string[]);
    for (const name of entries) {
      const info = await stat(path.join(dir, name)).catch(() => null);
      if (info && Date.now() - info.mtimeMs > config.retentionMs) {
        await rm(path.join(dir, name), { recursive: true, force: true });
      }
    }
  }
}
