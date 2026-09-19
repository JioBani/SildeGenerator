import Redis from 'ioredis';
import { redisConnection } from '../config/app-config';
import { mkdir, readFile, stat } from "node:fs/promises";
import { OnWorkerEvent, Processor, WorkerHost } from "@nestjs/bullmq";
import { Inject, Logger } from "@nestjs/common";
import type { Job } from "bullmq";
import { config } from "../config/app-config";
import { jobPaths, RENDER_QUEUE, type RenderJobData, type RenderJobProgress } from "../shared/render-job";
import { VIDEO_RUNNER, type VideoRunner } from "./runners/video-runner";
import { DatabaseService } from "../database/database.service";
import { MetricsService } from "../metrics/metrics.service";
import { failedStage, userFacingRunnerError } from "./runner-error";

@Processor(RENDER_QUEUE, { concurrency: config.concurrency, lockDuration: 120_000 })
export class RenderProcessor extends WorkerHost {
  private readonly redis = new Redis(redisConnection());
  onModuleDestroy() { this.redis.disconnect(); }
  private readonly logger = new Logger(RenderProcessor.name);

  constructor(
    @Inject(VIDEO_RUNNER) private readonly runner: VideoRunner,
    private readonly db: DatabaseService,
    private readonly metrics: MetricsService,
  ) {
    super();
  }

  async process(job: Job<RenderJobData>) {
    const paths = jobPaths(job.id!);
    await Promise.all([paths.work, paths.output, paths.logs].map((d) => mkdir(d, { recursive: true })));

    const startedAt = Date.now();
    const previous = await this.db.query<{ updated_at: Date }>(`SELECT updated_at FROM generation_jobs WHERE id=$1`, [job.id!]);
    const attempt = job.attemptsMade + 1;
    const waitStartedAt = attempt === 1 ? job.timestamp : new Date(previous.rows[0]?.updated_at ?? startedAt).getTime();
    const waitStage = attempt === 1 ? 'queue_wait' : 'retry_wait';
    await this.db.query(`UPDATE generation_jobs SET status='running',current_stage='job_initialization',progress=1,started_at=coalesce(started_at,now()),updated_at=now() WHERE id=$1`, [job.id!]);
    await this.db.query(`INSERT INTO job_stage_runs(job_id,stage,attempt,status,started_at,finished_at,duration_ms,metadata)
      VALUES($1,$2,$3,'completed',to_timestamp($4/1000.0),now(),$5,$6)`, [job.id!, waitStage, attempt, waitStartedAt, Math.max(0, startedAt - waitStartedAt), { bullJobId: job.id }]);
    await this.db.query(`INSERT INTO job_events(job_id,event_type,payload) VALUES($1,'started',$2)`, [job.id!, {
      attempt,
      queueWaitMs: Math.max(0, startedAt - waitStartedAt),
      videoJobGlobalConcurrency: config.videoJobGlobalConcurrency,
    }]);

    // 스킬이 progress.json 을 쓰면 주기적으로 반영
    const poll = setInterval(async () => {
      const raw = await readFile(paths.progress, "utf8").catch(() => null);
      if (!raw) return;
      try {
        const progress = JSON.parse(raw) as RenderJobProgress;
        await job.updateProgress(progress);
        await this.db.query(`UPDATE generation_jobs SET current_stage=$2,progress=$3,updated_at=now() WHERE id=$1`, [job.id!, progress.step, Math.min(99, Math.max(0, progress.percent ?? 0))]);
      } catch {}
    }, 3000);

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), config.jobTimeoutMs);
    try {
      await job.updateProgress({ step: "started", percent: 0 } satisfies RenderJobProgress);
      const result = await this.runner.run({
        jobId: job.id!,
        attempt,
        scenario: job.data.scenario,
        paths,
        signal: controller.signal,
        codexModel: job.data.codexModel,
        codexReasoningEffort: job.data.codexReasoningEffort,
        codexFastMode: job.data.codexFastMode,
        imageModel: job.data.imageModel,
        continuityEnabled: job.data.continuityEnabled ?? false,
        imageStyle: job.data.imageStyle ?? "editorial_illustration",
        voiceSettings: job.data.voiceSettings,
        harnessId: job.data.harnessId ?? "classic-slide",
        harnessSnapshot: job.data.harnessSnapshot,
      });
      await this.metrics.recordRunnerResult(job.id!, result.stages ?? [], result.usage ?? [], result.assets ?? [], result.prompts ?? []);
      if (result.narrative_blueprint) await this.db.query(`UPDATE generation_jobs SET narrative_blueprint=$2,updated_at=now() WHERE id=$1`, [job.id!, result.narrative_blueprint]);
      if (result.harness_snapshot) await this.db.query(`UPDATE generation_jobs SET harness_snapshot=$2::jsonb,updated_at=now() WHERE id=$1`, [job.id!, result.harness_snapshot]);
      if (!result.success) {
        const error = new Error(result.message || "runner reported failure") as Error & { runnerStage?: string };
        error.runnerStage = failedStage(result.stages);
        throw error;
      }
      const info = await stat(paths.video).catch(() => null);
      if (!info || info.size === 0) throw new Error(`output video missing: ${paths.video}`);
      await job.updateProgress({ step: "done", percent: 100 } satisfies RenderJobProgress);
      await this.db.query(`UPDATE generation_jobs SET status='completed',current_stage='done',progress=100,error_code=null,error_message=null,finished_at=now(),total_duration_ms=(extract(epoch FROM (now()-queued_at))*1000)::bigint,output_path=$2,updated_at=now() WHERE id=$1`, [job.id!, paths.video]);
      await this.db.query(`INSERT INTO job_events(job_id,event_type,payload) VALUES($1,'completed',$2)`, [job.id!, { attempt }]);
      return result;
    } catch (error) {
      const finalAttempt = attempt >= (job.opts.attempts ?? 1);
      const stage = error instanceof Error && "runnerStage" in error ? (error as Error & { runnerStage?: string }).runnerStage : undefined;
      const rawMessage = error instanceof Error ? error.message : String(error);
      const message = userFacingRunnerError(error, stage);
      await this.db.query(`UPDATE generation_jobs SET status=$2,current_stage=$3,error_code='RUNNER_ERROR',error_message=$4,finished_at=CASE WHEN $2='failed' THEN now() ELSE null END,total_duration_ms=CASE WHEN $2='failed' THEN (extract(epoch FROM (now()-queued_at))*1000)::bigint ELSE null END,updated_at=now() WHERE id=$1`, [job.id!, finalAttempt ? 'failed' : 'queued', finalAttempt ? (stage ?? 'failed') : 'retry_wait', message]);
      await this.db.query(`INSERT INTO job_events(job_id,event_type,payload) VALUES($1,$2,$3)`, [job.id!, finalAttempt ? 'failed' : 'retry_scheduled', { attempt, stage, message, rawMessage }]);
      throw error;
    } finally {
      clearInterval(poll);
      clearTimeout(timeout);
    }
  }

  private async release(job: Job<RenderJobData>) {
    const client = this.redis;
    await client.srem(`limits:pending:${job.data.userId}`, job.id!);
    await client.srem('limits:pending:global', job.id!);
  }

  @OnWorkerEvent("completed")
  async onCompleted(job: Job) {
    await this.release(job);
    this.logger.log(`job ${job.id} completed`);
  }

  @OnWorkerEvent("failed")
  async onFailed(job: Job | undefined, err: Error) {
    if (job && job.attemptsMade >= (job.opts.attempts ?? 1)) await this.release(job);
    this.logger.error(`job ${job?.id} failed: ${err.message}`);
  }
}
