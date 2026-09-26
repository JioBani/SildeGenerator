import Redis from 'ioredis';
import { randomUUID } from 'node:crypto';
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
import { releaseTime, settleTime } from "../wallet/time-wallet";

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
    await this.db.query(`UPDATE generation_jobs SET status='running',current_stage='job_initialization',progress=1,error_code=null,error_message=null,started_at=coalesce(started_at,now()),updated_at=now() WHERE id=$1`, [job.id!]);
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
    const timeout = setTimeout(() => controller.abort(), job.data.durationProfile === "single_30m" ? config.longFormJobTimeoutMs : config.jobTimeoutMs);
    try {
      await job.updateProgress({ step: "started", percent: 0 } satisfies RenderJobProgress);
      const result = await this.runner.run({
        jobId: job.id!,
        attempt,
        scenario: job.data.scenario,
        visualCues: job.data.visualCues ?? [],
        paths,
        signal: controller.signal,
        codexModel: job.data.codexModel,
        codexReasoningEffort: job.data.codexReasoningEffort,
        codexFastMode: job.data.codexFastMode,
        imageModel: job.data.imageModel,
        continuityEnabled: job.data.continuityEnabled ?? false,
        imageStyle: job.data.imageStyle ?? "editorial_illustration",
        motionStyle: job.data.motionStyle ?? null,
        slideVisualProfile: job.data.slideVisualProfile ?? null,
        musicSelection: job.data.musicSelection ?? { mode: "none" },
        genreId: job.data.genreId,
        genreVersion: job.data.genreVersion,
        voiceSettings: job.data.voiceSettings,
        harnessId: job.data.harnessId ?? "classic-slide",
        harnessSnapshot: job.data.harnessSnapshot,
        durationProfile: job.data.durationProfile ?? "episode_60",
        aspectRatio: job.data.aspectRatio ?? "16:9",
        subtitlesEnabled: job.data.subtitlesEnabled ?? true,
      });
      await this.metrics.recordRunnerResult(job.id!, result.stages ?? [], result.usage ?? [], result.assets ?? [], result.prompts ?? []);
      if (result.narrative_blueprint) await this.db.query(`UPDATE generation_jobs SET narrative_blueprint=$2,updated_at=now() WHERE id=$1`, [job.id!, result.narrative_blueprint]);
      if (result.harness_snapshot) await this.db.query(`UPDATE generation_jobs SET harness_snapshot=$2::jsonb,updated_at=now() WHERE id=$1`, [job.id!, result.harness_snapshot]);
      if (result.production_pack || result.quality_gate_report) await this.db.query(`UPDATE production_versions SET scene_plan=coalesce($2::jsonb,scene_plan),production_pack=coalesce($3::jsonb,production_pack),quality_gate_report=coalesce($4::jsonb,quality_gate_report),status=CASE WHEN $4::jsonb->>'status'='BLOCKED' THEN 'blocked' ELSE 'review_required' END,updated_at=now() WHERE job_id=$1`, [job.id!, result.narrative_blueprint ?? null, result.production_pack ?? null, result.quality_gate_report ?? null]);
      if (!result.success) {
        const error = new Error(result.message || "runner reported failure") as Error & { runnerStage?: string };
        error.runnerStage = failedStage(result.stages);
        throw error;
      }
      const info = await stat(paths.video).catch(() => null);
      if (!info || info.size === 0) throw new Error(`output video missing: ${paths.video}`);
      const finalVideo = result.assets?.find((asset) => asset.asset_type === 'final_video');
      await this.db.transaction(async (client) => {
        const version = await client.query<{ id: string; episode_id: string }>(`SELECT id,episode_id FROM production_versions WHERE job_id=$1`, [job.id!]);
        const current = version.rows[0];
        if (!current) return;
        const gateStatus = String(result.quality_gate_report?.status ?? 'TECHNICAL_PASS_HUMAN_PENDING');
        await client.query(`UPDATE production_versions SET status='review_required',updated_at=now() WHERE id=$1`, [current.id]);
        await client.query(`UPDATE episodes SET status='review_required',updated_at=now() WHERE id=$1`, [current.episode_id]);
        await client.query(`INSERT INTO quality_reviews(id,production_version_id,review_type,status,findings,evidence) VALUES($1,$2,'gold','PENDING','[]'::jsonb,$3::jsonb)
          ON CONFLICT(production_version_id,review_type) DO UPDATE SET status='PENDING',findings='[]'::jsonb,evidence=excluded.evidence,created_at=now()`, [randomUUID(),current.id,{ qualityGateStatus: gateStatus }]);
        await client.query(`INSERT INTO delivery_receipts(id,production_version_id,output_path,output_sha256,duration_ms,validation_status,manifest) VALUES($1,$2,$3,$4,$5,$6,$7::jsonb)
          ON CONFLICT(production_version_id) DO UPDATE SET output_path=excluded.output_path,output_sha256=excluded.output_sha256,duration_ms=excluded.duration_ms,validation_status=excluded.validation_status,manifest=excluded.manifest,created_at=now()`, [randomUUID(),current.id,paths.video,finalVideo?.sha256 ?? null,finalVideo?.duration_ms ?? null,gateStatus,{ harness: job.data.harnessSnapshot, motionStyle: job.data.motionStyle ?? null, slideVisualProfile: job.data.slideVisualProfile ?? null, musicSelection: job.data.musicSelection ?? { mode: "none" }, durationProfile: job.data.durationProfile, humanGoldReview: 'PENDING' }]);
      });
      await job.updateProgress({ step: "done", percent: 100 } satisfies RenderJobProgress);
      await this.db.transaction(async (client) => {
        if (config.timeWalletEnabled) await settleTime(client, job.id!, Number(finalVideo?.duration_ms) / 1000);
        await client.query(`UPDATE generation_jobs SET status='completed',current_stage='done',progress=100,error_code=null,error_message=null,finished_at=now(),total_duration_ms=(extract(epoch FROM (now()-queued_at))*1000)::bigint,output_path=$2,updated_at=now() WHERE id=$1`, [job.id!, paths.video]);
        await client.query(`INSERT INTO user_notifications(user_id,job_id,kind)
          SELECT user_id,id,'completed' FROM generation_jobs WHERE id=$1
          ON CONFLICT(user_id,job_id,kind) DO NOTHING`, [job.id!]);
        await client.query(`INSERT INTO job_events(job_id,event_type,payload) VALUES($1,'completed',$2)`, [job.id!, { attempt }]);
      });
      return result;
    } catch (error) {
      const finalAttempt = attempt >= (job.opts.attempts ?? 1);
      const stage = error instanceof Error && "runnerStage" in error ? (error as Error & { runnerStage?: string }).runnerStage : undefined;
      const rawMessage = error instanceof Error ? error.message : String(error);
      const message = userFacingRunnerError(error, stage);
      await this.db.query(`UPDATE generation_jobs SET status=$2,current_stage=$3,error_code='RUNNER_ERROR',error_message=$4,finished_at=CASE WHEN $2='failed' THEN now() ELSE null END,total_duration_ms=CASE WHEN $2='failed' THEN (extract(epoch FROM (now()-queued_at))*1000)::bigint ELSE null END,updated_at=now() WHERE id=$1`, [job.id!, finalAttempt ? 'failed' : 'queued', finalAttempt ? (stage ?? 'failed') : 'retry_wait', message]);
      await this.db.query(`INSERT INTO job_events(job_id,event_type,payload) VALUES($1,$2,$3)`, [job.id!, finalAttempt ? 'failed' : 'retry_scheduled', { attempt, stage, message, rawMessage }]);
      if (finalAttempt) await this.db.transaction(async (client) => {
        await client.query(`UPDATE production_versions SET status='failed',updated_at=now() WHERE job_id=$1`, [job.id!]);
        if (config.timeWalletEnabled) await releaseTime(client, job.id!);
      });
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
    if (job && job.attemptsMade >= (job.opts.attempts ?? 1)) {
      if (config.timeWalletEnabled) await this.db.transaction((client) => releaseTime(client, job.id!));
      await this.release(job);
    }
    this.logger.error(`job ${job?.id} failed: ${err.message}`);
  }
}
