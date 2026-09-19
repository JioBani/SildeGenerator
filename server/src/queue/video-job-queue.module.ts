import { BullModule } from "@nestjs/bullmq";
import { Module } from "@nestjs/common";
import { RENDER_QUEUE } from "../shared/render-job";
import { VideoJobQueueService } from "./video-job-queue.service";

@Module({
  imports: [BullModule.registerQueue({ name: RENDER_QUEUE })],
  providers: [VideoJobQueueService],
  exports: [VideoJobQueueService, BullModule],
})
export class VideoJobQueueModule {}
