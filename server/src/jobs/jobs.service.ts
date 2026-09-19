import { openVideo } from './safe-video';
import Redis from 'ioredis';
import { redisConnection } from '../config/app-config';
import { randomUUID } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";
import { InjectQueue } from "@nestjs/bullmq";
import { GoneException, HttpException, Injectable, NotFoundException } from "@nestjs/common";
import type { Queue } from "bullmq";
import { config } from "../config/app-config";
import { jobPaths, RENDER_QUEUE, type RenderJobData } from "../shared/render-job";
import { DatabaseService } from "../database/database.service";
import { CodexSettingsService } from "../settings/codex-settings.service";
import { DEFAULT_IMAGE_MODEL, type ImageModel } from "../shared/image-model";
import { DEFAULT_IMAGE_STYLE, type ImageStyle } from "../shared/image-style";
import { VideoJobQueueService } from "../queue/video-job-queue.service";
import { VoiceSettingsService } from "../settings/voice-settings.service";
import { DEFAULT_HARNESS_ID } from "../shared/harness";
import { HarnessRegistryService } from "./harness-registry.service";

@Injectable()
export class JobsService {
  private readonly redis = new Redis(redisConnection());
  onModuleDestroy() { this.redis.disconnect(); }
  constructor(
    @InjectQueue(RENDER_QUEUE) private readonly queue: Queue<RenderJobData>,
    private readonly db: DatabaseService,
    private readonly codexSettings: CodexSettingsService,
    private readonly videoQueue: VideoJobQueueService,
    private readonly voiceSettings: VoiceSettingsService,
    private readonly harnessRegistry: HarnessRegistryService,
  ) {}

  harnesses() { return this.harnessRegistry.list(); }

  async create(scenario: string, userId: string, imageModel: ImageModel = DEFAULT_IMAGE_MODEL, continuityEnabled = false, imageStyle: ImageStyle = DEFAULT_IMAGE_STYLE, harnessId = DEFAULT_HARNESS_ID) {
    const id = randomUUID();
    const runtime = await this.codexSettings.get();
    const voice = await this.voiceSettings.snapshot();
    const harness = await this.harnessRegistry.resolve(harnessId);
    const client = this.redis;
    const dayKey = `limits:daily:${userId}:${new Date().toISOString().slice(0, 10)}`;
    const userKey = `limits:pending:${userId}`;
    const result = await client.eval(`
      local daily_limit = tonumber(ARGV[1])
      if daily_limit > 0 and tonumber(redis.call('GET', KEYS[1]) or '0') >= daily_limit then return 1 end
      if redis.call('SCARD',KEYS[3]) >= tonumber(ARGV[3]) then return 3 end
      if redis.call('SCARD',KEYS[2]) >= tonumber(ARGV[2]) then return 2 end
      if daily_limit > 0 then
        redis.call('INCR',KEYS[1]); redis.call('EXPIRE',KEYS[1],172800)
      end
      redis.call('SADD',KEYS[2],ARGV[4]); redis.call('SADD',KEYS[3],ARGV[4]); return 0
    `, 3, dayKey, userKey, 'limits:pending:global', config.dailyJobs, config.userPending, config.globalPending, id);
    if (Number(result)) throw new HttpException([
      '',
      '오늘 생성할 수 있는 영상 수를 모두 사용했습니다.',
      '이미 처리 중인 작업이 있습니다. 완료된 뒤 다시 시도해 주세요.',
      '현재 작업 대기열이 가득 찼습니다. 잠시 후 다시 시도해 주세요.',
    ][Number(result)], 429);
    // Keep reservations charged on ambiguous failures (fail closed).
    const paths = jobPaths(id);
    await mkdir(paths.input, { recursive: true });
    await writeFile(paths.scenario, scenario, "utf8");

    await this.db.query(`INSERT INTO generation_jobs(id,user_id,scenario,status,current_stage,progress,codex_model,codex_effort,codex_fast_mode,image_model,continuity_enabled,video_fps,voice_concurrency,image_style,voice_provider,voice_model,voice_id,voice_settings,voice_settings_version,harness_id,harness_version,harness_manifest_sha256,harness_source_sha256,harness_config_sha256,harness_source_revision,harness_image_digest,harness_snapshot)
      VALUES($1,$2,$3,'queued','queue_wait',0,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,$24::jsonb)`, [id,userId,scenario,runtime.model,runtime.effort,runtime.fastMode,imageModel,continuityEnabled,config.videoFps,config.voiceConcurrency,imageStyle,voice.provider,voice.model,voice.voiceId,voice,voice.version,harness.id,harness.version,harness.manifest_sha256,harness.source_sha256,harness.config_sha256,harness.source_revision,harness.image_digest,harness]);

    const retentionSec = config.retentionMs / 1000;
    try {
      await this.queue.add("render", {
        scenario,
        userId,
        codexModel: runtime.model,
        codexReasoningEffort: runtime.effort,
        codexFastMode: runtime.fastMode,
        imageModel,
        continuityEnabled,
        imageStyle,
        voiceSettings: voice,
        harnessId: harness.id,
        harnessSnapshot: harness,
      }, {
        jobId: id,
        attempts: 2,
        backoff: { type: "exponential", delay: 5000 },
        removeOnComplete: { age: retentionSec },
        removeOnFail: { age: retentionSec },
      });
    } catch (error) {
      await this.db.query(`UPDATE generation_jobs SET status='failed',error_code='QUEUE_ERROR',error_message=$2,finished_at=now(),updated_at=now() WHERE id=$1`, [id, error instanceof Error ? error.message : String(error)]);
      throw error;
    }
    const queue = await this.videoQueue.safeSnapshot(id);
    await this.db.query(`INSERT INTO job_events(job_id,event_type,payload) VALUES($1,'queued',$2)`, [id, {
      queuePosition: queue?.queuePosition ?? null,
      jobsAhead: queue?.jobsAhead ?? null,
      activeJobs: queue?.activeJobs ?? null,
      queuedJobs: queue?.queuedJobs ?? null,
    }]);
    const running = queue?.activeJobIds.includes(id) ?? false;
    return {
      id,
      status: running ? 'running' : 'queued',
      currentStage: running ? 'job_initialization' : 'queue_wait',
      progress: running ? 1 : 0,
      imageModel,
      continuityEnabled,
      imageStyle,
      voiceProvider: voice.provider,
      voiceModel: voice.model,
      voiceId: voice.voiceId,
      harnessId: harness.id,
      harnessVersion: harness.version,
      queuePosition: running ? null : queue?.queuePosition ?? null,
      jobsAhead: running ? 0 : queue?.jobsAhead ?? null,
      activeJobs: queue?.activeJobs ?? null,
      queuedJobs: queue?.queuedJobs ?? null,
    };
  }

  async get(id: string, userId: string) {
    const result = await this.db.query(`SELECT id,status,current_stage AS "currentStage",progress,error_message AS error,queued_at AS "queuedAt",started_at AS "startedAt",finished_at AS "finishedAt",total_duration_ms AS "totalDurationMs",image_model AS "imageModel",image_style AS "imageStyle",continuity_enabled AS "continuityEnabled",video_fps AS "videoFps",voice_concurrency AS "voiceConcurrency",voice_provider AS "voiceProvider",voice_model AS "voiceModel",voice_id AS "voiceId",harness_id AS "harnessId",harness_version AS "harnessVersion" FROM generation_jobs WHERE id=$1 AND user_id=$2`, [id,userId]);
    if (!result.rowCount) throw new NotFoundException();
    const job = result.rows[0];
    const queue = await this.videoQueue.safeSnapshot(id);
    const activeInQueue = queue?.activeJobIds.includes(id) ?? false;
    const effectiveStatus = activeInQueue ? 'running' : job.status;
    const queued = effectiveStatus === 'queued' || effectiveStatus === 'waiting';
    const running = effectiveStatus === 'running';
    return {
      ...job,
      status: effectiveStatus,
      queuePosition: queued ? queue?.queuePosition ?? null : null,
      jobsAhead: queued ? queue?.jobsAhead ?? null : running ? 0 : null,
      activeJobs: queue?.activeJobs ?? null,
      queuedJobs: queue?.queuedJobs ?? null,
    };
  }

  async getVideo(id: string, userId: string) {
    const result = await this.db.query(`SELECT status FROM generation_jobs WHERE id=$1 AND user_id=$2`, [id,userId]);
    if (!result.rowCount || result.rows[0].status !== "completed") throw new NotFoundException("video not ready");
    try { return await openVideo(id); } catch { throw new GoneException("video expired"); }
  }
}
