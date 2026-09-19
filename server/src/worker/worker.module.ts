import { BullModule } from "@nestjs/bullmq";
import { Module } from "@nestjs/common";
import { redisConnection } from "../config/app-config";
import { JobCleanupService } from "./job-cleanup.service";
import { RenderProcessor } from "./render.processor";
import { VIDEO_RUNNER } from "./runners/video-runner";
import { HttpRunner } from "./runners/http.runner";
import { DatabaseModule } from "../database/database.module";
import { MetricsModule } from "../metrics/metrics.module";
import { VideoJobQueueModule } from "../queue/video-job-queue.module";

@Module({
  imports: [
    DatabaseModule,
    MetricsModule,
    BullModule.forRoot({ connection: redisConnection() }),
    VideoJobQueueModule,
  ],
  providers: [
    RenderProcessor,
    JobCleanupService,
    { provide: VIDEO_RUNNER, useClass: HttpRunner },
  ],
})
export class WorkerModule {}
