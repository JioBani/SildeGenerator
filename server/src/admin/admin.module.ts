import { Module } from "@nestjs/common";
import { AdminController } from "./admin.controller";
import { PromptsService } from "./prompts.service";
import { AnalyticsService } from "./analytics.service";
import { VideoJobQueueModule } from "../queue/video-job-queue.module";

@Module({ imports: [VideoJobQueueModule], controllers: [AdminController], providers: [PromptsService, AnalyticsService] })
export class AdminModule {}
