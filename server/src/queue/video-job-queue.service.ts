import { InjectQueue } from "@nestjs/bullmq";
import { Injectable, Logger, OnModuleInit } from "@nestjs/common";
import type { Job, Queue } from "bullmq";
import { config } from "../config/app-config";
import { RENDER_QUEUE, type RenderJobData } from "../shared/render-job";

export type VideoQueueSnapshot = {
  queuePosition: number | null;
  jobsAhead: number | null;
  activeJobs: number;
  queuedJobs: number;
  oldestWaitMs: number | null;
  globalConcurrency: number;
  activeJobIds: string[];
  queuedJobIds: string[];
};

export function positionForJob(activeIds: string[], queuedIds: string[], jobId?: string) {
  if (!jobId) return { queuePosition: null, jobsAhead: null };
  if (activeIds.includes(jobId)) return { queuePosition: null, jobsAhead: 0 };
  const index = queuedIds.indexOf(jobId);
  return index < 0
    ? { queuePosition: null, jobsAhead: null }
    : { queuePosition: index + 1, jobsAhead: activeIds.length + index };
}

@Injectable()
export class VideoJobQueueService implements OnModuleInit {
  private readonly logger = new Logger(VideoJobQueueService.name);

  constructor(@InjectQueue(RENDER_QUEUE) private readonly queue: Queue<RenderJobData>) {}

  async onModuleInit() {
    await this.queue.setGlobalConcurrency(config.videoJobGlobalConcurrency);
    this.logger.log(`videoJobGlobalConcurrency=${config.videoJobGlobalConcurrency}`);
  }

  async snapshot(jobId?: string): Promise<VideoQueueSnapshot> {
    const limit = Math.max(config.globalPending, config.userPending) + 5;
    const [active, prioritized, waiting, delayed, configured] = await Promise.all([
      this.queue.getActive(0, limit),
      this.queue.getPrioritized(0, limit),
      this.queue.getWaiting(0, limit),
      this.queue.getDelayed(0, limit),
      this.queue.getGlobalConcurrency(),
    ]);
    const activeJobIds = this.ids(active);
    // BullMQ schedules priority jobs before the normal FIFO list. Delayed jobs
    // are ordered by their due timestamp and become eligible after ready jobs.
    const queued = this.uniqueJobs([...prioritized, ...waiting, ...delayed]);
    const queuedJobIds = this.ids(queued);
    const position = positionForJob(activeJobIds, queuedJobIds, jobId);
    const oldest = queued.reduce((value, job) => Math.min(value, job.timestamp), Number.POSITIVE_INFINITY);
    return {
      ...position,
      activeJobs: activeJobIds.length,
      queuedJobs: queuedJobIds.length,
      oldestWaitMs: Number.isFinite(oldest) ? Math.max(0, Date.now() - oldest) : null,
      globalConcurrency: configured ?? config.videoJobGlobalConcurrency,
      activeJobIds,
      queuedJobIds,
    };
  }

  async safeSnapshot(jobId?: string): Promise<VideoQueueSnapshot | null> {
    try {
      return await this.snapshot(jobId);
    } catch (error) {
      this.logger.error(`video queue state unavailable: ${error instanceof Error ? error.message : String(error)}`);
      return null;
    }
  }

  private ids(jobs: Array<Job<RenderJobData>>) {
    return jobs.map((job) => String(job.id));
  }

  private uniqueJobs(jobs: Array<Job<RenderJobData>>) {
    const seen = new Set<string>();
    return jobs.filter((job) => {
      const id = String(job.id);
      if (seen.has(id)) return false;
      seen.add(id);
      return true;
    });
  }
}
