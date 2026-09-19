import { Module } from "@nestjs/common";
import { VideoJobQueueModule } from "../queue/video-job-queue.module";
import { JobsController } from "./jobs.controller";
import { JobsService } from "./jobs.service";
import { HarnessRegistryService } from "./harness-registry.service";

@Module({
  imports: [VideoJobQueueModule],
  controllers: [JobsController],
  providers: [JobsService, HarnessRegistryService],
  exports: [JobsService],
})
export class JobsModule {}
