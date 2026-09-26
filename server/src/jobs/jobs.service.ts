import { openVideo } from './safe-video';
import { openThumbnail } from './safe-thumbnail';
import Redis from 'ioredis';
import { redisConnection } from '../config/app-config';
import { createHash, randomUUID } from "node:crypto";
import { mkdir, writeFile, stat } from "node:fs/promises";
import path from "node:path";
import { InjectQueue } from "@nestjs/bullmq";
import { BadRequestException, GoneException, HttpException, Injectable, NotFoundException } from "@nestjs/common";
import type { Queue } from "bullmq";
import { config } from "../config/app-config";
import { jobPaths, RENDER_QUEUE, type RenderJobData } from "../shared/render-job";
import { DatabaseService } from "../database/database.service";
import { CodexSettingsService } from "../settings/codex-settings.service";
import { DEFAULT_IMAGE_MODEL, type ImageModel } from "../shared/image-model";
import { DEFAULT_IMAGE_STYLE, type ImageStyle } from "../shared/image-style";
import { motionStyleSnapshot, type MotionStyleId, type MotionStyleSnapshot } from "../shared/motion-style";
import { slideVisualProfile, type SlideVisualProfile } from "../shared/slide-visual-profile";
import { autoMusicPreset, publicMusicSelection, type MusicSelection } from "../shared/music-selection";
import { audioFormat } from "./music-upload";
import { VideoJobQueueService } from "../queue/video-job-queue.service";
import { VoiceSettingsService } from "../settings/voice-settings.service";
import { DEFAULT_HARNESS_ID } from "../shared/harness";
import { HarnessRegistryService } from "./harness-registry.service";
import { applyNarrationSpeed, DEFAULT_NARRATION_SPEED } from "../shared/voice-settings";
import { prepareScenarioInput } from "../shared/scenario-input";
import { durationProfileForHarness, estimatedNarrationSeconds, maximumSeconds } from "../shared/duration-policy";
import type { CodexRuntimeSettings } from "../settings/codex-settings.service";
import type { VoiceSettingsSnapshot } from "../shared/voice-settings";
import type { HarnessSnapshot } from "../shared/harness";
import { releaseTime, reserveTime } from "../wallet/time-wallet";

type RemakeSource = {
  id: string;
  runtime: CodexRuntimeSettings;
  voice: VoiceSettingsSnapshot;
  harness: HarnessSnapshot;
  slideVisualProfile: SlideVisualProfile | null;
  musicSelection: MusicSelection;
};

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

  async uploadMusic(userId: string, file?: { buffer: Buffer; originalname: string }) {
    if (!config.slideV05LocalImages) throw new BadRequestException("음악 업로드 기능이 활성화되지 않았습니다.");
    if (!file?.buffer) throw new BadRequestException("음악 파일을 선택해 주세요.");
    const format = audioFormat(file.buffer);
    const id = randomUUID();
    const storage = path.join(config.dataDir, "music-uploads", `${id}${format.extension}`);
    await mkdir(path.dirname(storage), { recursive: true });
    await writeFile(storage, file.buffer, { flag: "wx" });
    const digest = createHash("sha256").update(file.buffer).digest("hex");
    const name = path.basename(file.originalname).slice(0, 255) || `music${format.extension}`;
    await this.db.query(`INSERT INTO music_uploads(id,user_id,original_name,mime_type,size_bytes,sha256,storage_path)
      VALUES($1,$2,$3,$4,$5,$6,$7)`, [id, userId, name, format.mimeType, file.buffer.length, digest, storage]);
    return { id, name, mimeType: format.mimeType, sizeBytes: file.buffer.length, sha256: digest };
  }

  async getMusicUpload(userId: string, id: string) {
    const result = await this.db.query<{ storage_path: string; mime_type: string; original_name: string }>(
      `SELECT storage_path,mime_type,original_name FROM music_uploads WHERE id=$1 AND user_id=$2 AND deleted_at IS NULL`, [id, userId]);
    const upload = result.rows[0];
    if (!upload) throw new NotFoundException("음악 파일을 찾을 수 없습니다.");
    const root = path.resolve(config.dataDir, "music-uploads") + path.sep;
    if (!path.resolve(upload.storage_path).startsWith(root)) throw new NotFoundException();
    return { path: upload.storage_path, mimeType: upload.mime_type, name: upload.original_name };
  }

  async deleteMusicUpload(userId: string, id: string) {
    const result = await this.db.query(`UPDATE music_uploads SET deleted_at=now()
      WHERE id=$1 AND user_id=$2 AND deleted_at IS NULL RETURNING id`, [id, userId]);
    if (!result.rowCount) throw new NotFoundException();
    return { deleted: true };
  }

  private async selectMusic(userId: string, mode: "none" | "auto" | "upload", uploadId: string | undefined,
                            scenario: string, style: ImageStyle): Promise<MusicSelection> {
    if (mode === "none") return { mode: "none" };
    if (!config.slideV05LocalImages) throw new BadRequestException("음악 기능이 활성화되지 않았습니다.");
    if (mode === "auto") return { mode, preset: autoMusicPreset(scenario, style) };
    if (!uploadId) throw new BadRequestException("사용할 음악 파일을 먼저 올려 주세요.");
    const result = await this.db.query<{ storage_path: string; sha256: string; mime_type: string }>(
      `SELECT storage_path,sha256,mime_type FROM music_uploads WHERE id=$1 AND user_id=$2 AND deleted_at IS NULL`, [uploadId, userId]);
    const upload = result.rows[0];
    if (!upload) throw new BadRequestException("선택한 음악 파일을 사용할 수 없습니다.");
    const root = path.resolve(config.dataDir, "music-uploads") + path.sep;
    if (!path.resolve(upload.storage_path).startsWith(root) || !(await stat(upload.storage_path).catch(() => null))) {
      throw new BadRequestException("음악 파일을 찾을 수 없습니다.");
    }
    return { mode, uploadId, path: upload.storage_path, sha256: upload.sha256, mimeType: upload.mime_type };
  }

  estimate(scenario: string, narrationSpeed: number, harnessId = "classic-slide") {
    let parsed;
    try { parsed = prepareScenarioInput(scenario); }
    catch { throw new BadRequestException("읽을 나레이션 문장을 입력해 주세요."); }
    return {
      title: parsed.title ?? null,
      narrationText: parsed.scenario,
      narrationChars: parsed.scenario.length,
      estimatedSeconds: estimatedNarrationSeconds(parsed.scenario, narrationSpeed, config.voiceProvider),
      maximumSeconds: maximumSeconds(durationProfileForHarness(harnessId)),
    };
  }

  async list(userId: string, offset = 0) {
    const result = await this.db.query(`SELECT job.id,coalesce(project.title,job.title,'새 영상') AS title,
      job.status,job.current_stage AS "currentStage",job.progress,job.error_message AS error,
      job.queued_at AS "queuedAt",job.finished_at AS "finishedAt",
      job.duration_profile AS "durationProfile",asset.duration_ms AS "videoDurationMs",
      EXISTS(SELECT 1 FROM generated_assets image WHERE image.job_id=job.id AND image.asset_type='scene_image' AND image.scene_id='scene-001') AS "hasThumbnail"
      FROM generation_jobs job
      LEFT JOIN video_projects project ON project.id=job.project_id
      LEFT JOIN LATERAL (SELECT duration_ms FROM generated_assets WHERE job_id=job.id AND asset_type='final_video' ORDER BY created_at DESC LIMIT 1) asset ON true
      WHERE job.user_id=$1 ORDER BY job.queued_at DESC,job.id DESC LIMIT 50 OFFSET $2`, [userId, offset]);
    return result.rows;
  }

  async notifications(userId: string) {
    const result = await this.db.query(`SELECT notification.id::text,notification.job_id AS "jobId",
      coalesce(project.title,'영상') AS title,notification.kind,
      notification.created_at AS "createdAt"
      FROM user_notifications notification
      JOIN generation_jobs job ON job.id=notification.job_id
      LEFT JOIN video_projects project ON project.id=job.project_id
      WHERE notification.user_id=$1 AND notification.read_at IS NULL
      ORDER BY notification.created_at DESC LIMIT 20`, [userId]);
    return result.rows;
  }

  async wallet(userId: string) {
    if (!config.timeWalletEnabled) return { enabled: false };
    const result = await this.db.query<{ balance_seconds: string; reserved_seconds: string }>(
      `SELECT balance_seconds,reserved_seconds FROM time_wallets WHERE user_id=$1`, [userId]);
    const balanceSeconds = Number(result.rows[0]?.balance_seconds ?? 0);
    const reservedSeconds = Number(result.rows[0]?.reserved_seconds ?? 0);
    return { enabled: true, balanceSeconds, reservedSeconds, availableSeconds: balanceSeconds - reservedSeconds };
  }

  async readNotification(userId: string, notificationId: string) {
    await this.db.query(`UPDATE user_notifications SET read_at=now() WHERE id=$1 AND user_id=$2`, [notificationId, userId]);
    return { ok: true };
  }

  async remake(id: string, userId: string) {
    const result = await this.db.query<{
      id: string; scenario_input: string | null; scenario: string;
      image_model: ImageModel; continuity_enabled: boolean; image_style: ImageStyle; motion_style: MotionStyleSnapshot | null; slide_visual_profile: SlideVisualProfile | null; music_selection: MusicSelection | null;
      harness_id: string; harness_snapshot: HarnessSnapshot; narration_speed: string;
      aspect_ratio: "16:9" | "9:16"; subtitles_enabled: boolean;
      voice_settings: VoiceSettingsSnapshot; codex_model: string;
      codex_effort: CodexRuntimeSettings["effort"]; codex_fast_mode: boolean;
    }>(`SELECT id,scenario_input,scenario,image_model,continuity_enabled,image_style,motion_style,slide_visual_profile,music_selection,harness_id,harness_snapshot,
      narration_speed,aspect_ratio,subtitles_enabled,voice_settings,codex_model,codex_effort,codex_fast_mode
      FROM generation_jobs WHERE id=$1 AND user_id=$2`, [id, userId]);
    const source = result.rows[0];
    if (!source) throw new NotFoundException("이전 작업을 찾을 수 없습니다.");
    if (!source.harness_snapshot?.source_sha256 || !source.voice_settings?.provider || !source.codex_model) {
      throw new HttpException("이 작업에는 동일 설정으로 다시 만들기 위한 기록이 부족합니다.", 409);
    }
    return this.create(source.scenario_input ?? source.scenario, userId, source.image_model,
      source.continuity_enabled, source.image_style, source.harness_id, Number(source.narration_speed),
      source.aspect_ratio, source.subtitles_enabled, {
        id: source.id,
        runtime: { model: source.codex_model, effort: source.codex_effort, fastMode: source.codex_fast_mode },
        voice: source.voice_settings,
        harness: source.harness_snapshot,
        slideVisualProfile: source.slide_visual_profile,
        musicSelection: source.music_selection ?? { mode: "none" },
      }, source.motion_style?.id, source.slide_visual_profile?.id);
  }

  async create(scenario: string, userId: string, imageModel: ImageModel = DEFAULT_IMAGE_MODEL, continuityEnabled = false, imageStyle: ImageStyle | undefined = undefined, harnessId: string | undefined = undefined, narrationSpeed = DEFAULT_NARRATION_SPEED, aspectRatio: "16:9" | "9:16" = "16:9", subtitlesEnabled = true, remakeSource?: RemakeSource, motionStyleId?: MotionStyleId, sceneVisualMode?: "local_illustration", musicMode: "none" | "auto" | "upload" = "none", musicUploadId?: string) {
    let preparedScenario;
    try { preparedScenario = prepareScenarioInput(scenario); }
    catch { throw new BadRequestException("읽을 나레이션 문장을 입력해 주세요."); }
    const productionScenario = preparedScenario.scenario;
    const resolvedHarnessId = harnessId ?? DEFAULT_HARNESS_ID;
    const mockSlideOnly = config.slideV05LocalImages && config.imageProvider === "mock";
    if (mockSlideOnly && resolvedHarnessId !== "classic-slide") {
      throw new BadRequestException("이 시험 사이트에서는 로컬 장면 삽화를 사용하는 슬라이드 영상만 제작할 수 있습니다.");
    }
    if (mockSlideOnly && sceneVisualMode !== "local_illustration") {
      throw new BadRequestException("AI 장면 이미지가 연결되지 않았습니다. 로컬 도형 삽화 시험 옵션을 직접 선택해 주세요.");
    }
    if (config.imageProvider === "local_graphic" && (resolvedHarnessId !== "astra-motion" || !motionStyleId)) {
      throw new BadRequestException("로컬 그래픽 시험 경로는 모션그래픽 제작 스타일이 필요합니다.");
    }
    if (motionStyleId && resolvedHarnessId !== "astra-motion") throw new BadRequestException("모션 제작 스타일은 모션그래픽에서만 사용할 수 있습니다.");
    if (resolvedHarnessId === "astra-motion" && config.motionLocalProduction && config.runnerMode !== "live") {
      throw new BadRequestException("이 시험 환경에서는 모션 장면 설계가 비활성화되어 있습니다. 실제 모션 제작에는 감독 설계 연결이 필요합니다.");
    }
    const motionStyle = motionStyleId ? motionStyleSnapshot(motionStyleId, config.motionLocalProduction) : null;
    if (motionStyle?.productionRoute === "local_graphic") continuityEnabled = false;
    if (sceneVisualMode && !config.slideV05LocalImages) throw new BadRequestException("로컬 장면 삽화 기능이 아직 활성화되지 않았습니다.");
    if (sceneVisualMode && resolvedHarnessId !== "classic-slide") throw new BadRequestException("로컬 장면 삽화는 기본 슬라이드에서만 사용할 수 있습니다.");
    const durationProfile = durationProfileForHarness(resolvedHarnessId);
    if (estimatedNarrationSeconds(productionScenario, narrationSpeed, config.voiceProvider) > maximumSeconds(durationProfile)) {
      throw new HttpException(durationProfile === "single_30m"
        ? "예상 영상 길이가 30분을 넘습니다. 대본을 줄이거나 나레이션 속도를 높여 주세요."
        : "예상 영상 길이가 60초를 넘습니다.", 400);
    }
    const resolvedImageStyle = motionStyle?.imagePreset ?? imageStyle ?? DEFAULT_IMAGE_STYLE;
    if (config.imageProvider === "oauth" && !sceneVisualMode && motionStyle?.productionRoute !== "local_graphic" && imageModel !== "gpt-image-2") {
      throw new BadRequestException("현재 구독 이미지 연결은 GPT Image 2만 지원합니다.");
    }
    if (config.imageProvider === "oauth" && !sceneVisualMode && motionStyle?.productionRoute !== "local_graphic"
        && Date.now() / 1000 < config.imageGenerationPausedUntilUnix) {
      const reset = new Date(config.imageGenerationPausedUntilUnix * 1000).toLocaleString("ko-KR", { timeZone: "Asia/Seoul" });
      throw new HttpException(`구독 이미지 생성 한도에 도달했습니다. ${reset} 이후 다시 시도해 주세요.`, 503);
    }
    if (sceneVisualMode && resolvedImageStyle !== "cute_character" && resolvedImageStyle !== "fantasy_anime") {
      throw new BadRequestException("로컬 장면 삽화는 따뜻한 캐릭터와 판타지 화풍에서만 지원합니다.");
    }
    const slideProfile = sceneVisualMode ? slideVisualProfile(resolvedImageStyle) : null;
    if (slideProfile) continuityEnabled = false;
    if (musicMode !== "none" && resolvedHarnessId !== "classic-slide") throw new BadRequestException("배경음악 시험 기능은 기본 슬라이드에서만 사용할 수 있습니다.");
    const musicSelection = remakeSource?.musicSelection ?? await this.selectMusic(userId, musicMode, musicUploadId, productionScenario, resolvedImageStyle);
    const id = randomUUID();
    const projectId = randomUUID();
    const episodeId = randomUUID();
    const productionVersionId = randomUUID();
    const runtime = remakeSource?.runtime ?? await this.codexSettings.get();
    const voice = remakeSource?.voice ?? applyNarrationSpeed(await this.voiceSettings.snapshot(), narrationSpeed);
    const harness = await this.harnessRegistry.resolve(resolvedHarnessId);
    if (remakeSource && ["version", "manifest_sha256", "source_sha256", "config_sha256"].some((key) =>
      harness[key as keyof HarnessSnapshot] !== remakeSource.harness[key as keyof HarnessSnapshot])) {
      throw new HttpException("이 영상의 제작 버전이 현재 설치되어 있지 않습니다. 이전 버전을 복원한 뒤 다시 시도해 주세요.", 409);
    }
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
    await writeFile(paths.scenario, productionScenario, "utf8");

    const title = preparedScenario.title?.slice(0, 120)
      || productionScenario.split(/\r?\n/).map((line) => line.trim()).find(Boolean)?.slice(0, 120)
      || "새 영상";
    try { await this.db.transaction(async (client) => {
      await client.query(`INSERT INTO video_projects(id,user_id,title,status) VALUES($1,$2,$3,'active')`, [projectId,userId,title]);
      await client.query(`INSERT INTO episodes(id,project_id,ordinal,title,status,duration_profile,target_seconds,maximum_seconds) VALUES($1,$2,1,$3,'production_requested',$4,$5,$6)`, [episodeId,projectId,title,durationProfile,durationProfile === "single_30m" ? 1800 : 50,maximumSeconds(durationProfile)]);
      await client.query(`INSERT INTO generation_jobs(id,user_id,scenario,status,current_stage,progress,codex_model,codex_effort,codex_fast_mode,image_model,continuity_enabled,video_fps,voice_concurrency,image_style,voice_provider,voice_model,voice_id,voice_settings,voice_settings_version,narration_speed,harness_id,harness_version,harness_manifest_sha256,harness_source_sha256,harness_config_sha256,harness_source_revision,harness_image_digest,harness_snapshot,project_id,episode_id,duration_profile,aspect_ratio,subtitles_enabled,scenario_input,remake_of_job_id,motion_style,slide_visual_profile,music_selection)
        VALUES($1,$2,$3,'queued','queue_wait',0,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,$24,$25::jsonb,$26,$27,$28,$29,$30,$31,$32,$33::jsonb,$34::jsonb,$35::jsonb)`, [id,userId,productionScenario,runtime.model,runtime.effort,runtime.fastMode,imageModel,continuityEnabled,config.videoFps,config.voiceConcurrency,resolvedImageStyle,voice.provider,voice.model,voice.voiceId,voice,voice.version,narrationSpeed,harness.id,harness.version,harness.manifest_sha256,harness.source_sha256,harness.config_sha256,harness.source_revision,harness.image_digest,harness,projectId,episodeId,durationProfile,aspectRatio,subtitlesEnabled,scenario,remakeSource?.id ?? null,motionStyle ? JSON.stringify(motionStyle) : null,slideProfile ? JSON.stringify(slideProfile) : null,JSON.stringify(musicSelection)]);
      await client.query(`INSERT INTO production_versions(id,episode_id,job_id,version,status) VALUES($1,$2,$3,1,'queued')`, [productionVersionId,episodeId,id]);
      await client.query(`UPDATE generation_jobs SET production_version_id=$2 WHERE id=$1`, [id,productionVersionId]);
      if (config.timeWalletEnabled) await reserveTime(client, userId, id, estimatedNarrationSeconds(productionScenario, narrationSpeed, config.voiceProvider));
    }); } catch (error) {
      await this.redis.srem(userKey, id);
      await this.redis.srem('limits:pending:global', id);
      if (config.dailyJobs > 0) await this.redis.decr(dayKey);
      throw error;
    }

    const retentionSec = config.retentionMs / 1000;
    try {
      await this.queue.add("render", {
        scenario: productionScenario,
        visualCues: preparedScenario.visualCues,
        userId,
        codexModel: runtime.model,
        codexReasoningEffort: runtime.effort,
        codexFastMode: runtime.fastMode,
        imageModel,
        continuityEnabled,
        imageStyle: resolvedImageStyle,
        motionStyle,
        slideVisualProfile: slideProfile,
        musicSelection,
        voiceSettings: voice,
        narrationSpeed,
        harnessId: harness.id,
        harnessSnapshot: harness,
        durationProfile,
        aspectRatio,
        subtitlesEnabled,
      }, {
        jobId: id,
        attempts: 2,
        backoff: { type: "exponential", delay: 5000 },
        removeOnComplete: { age: retentionSec },
        removeOnFail: { age: retentionSec },
      });
    } catch (error) {
      let confirmedAbsent = false;
      try { confirmedAbsent = !(await this.queue.getJob(id)); } catch { /* An unknown enqueue outcome retains the reservation. */ }
      if (confirmedAbsent) {
        await this.db.transaction(async (client) => {
          await client.query(`UPDATE generation_jobs SET status='failed',error_code='QUEUE_ERROR',error_message=$2,finished_at=now(),updated_at=now() WHERE id=$1`, [id, error instanceof Error ? error.message : String(error)]);
          await client.query(`UPDATE production_versions SET status='failed',updated_at=now() WHERE id=$1`, [productionVersionId]);
          await client.query(`UPDATE episodes SET status='failed',updated_at=now() WHERE id=$1`, [episodeId]);
          if (config.timeWalletEnabled) await releaseTime(client, id);
        });
        await this.redis.srem(userKey, id);
        await this.redis.srem('limits:pending:global', id);
        throw error;
      }
      await this.db.query(`INSERT INTO job_events(job_id,event_type,payload) VALUES($1,'queue_confirmation_needed',$2)`, [id, { message: error instanceof Error ? error.message : String(error) }]);
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
      imageStyle: resolvedImageStyle,
      motionStyle,
      slideVisualProfile: slideProfile,
      musicSelection: publicMusicSelection(musicSelection),
      voiceProvider: voice.provider,
      voiceModel: voice.model,
      voiceId: voice.voiceId,
      narrationSpeed,
      harnessId: harness.id,
      harnessVersion: harness.version,
      episodeNumber: 1,
      durationProfile,
      aspectRatio,
      subtitlesEnabled,
      queuePosition: running ? null : queue?.queuePosition ?? null,
      jobsAhead: running ? 0 : queue?.jobsAhead ?? null,
      activeJobs: queue?.activeJobs ?? null,
      queuedJobs: queue?.queuedJobs ?? null,
    };
  }

  async get(id: string, userId: string) {
    const result = await this.db.query(`SELECT job.id,job.genre_id AS "genreId",job.genre_version AS "genreVersion",job.status,job.current_stage AS "currentStage",job.progress,job.error_message AS error,job.queued_at AS "queuedAt",job.started_at AS "startedAt",job.finished_at AS "finishedAt",job.total_duration_ms AS "totalDurationMs",job.image_model AS "imageModel",job.image_style AS "imageStyle",job.motion_style AS "motionStyle",job.slide_visual_profile AS "slideVisualProfile",job.music_selection AS "musicSelection",job.continuity_enabled AS "continuityEnabled",job.video_fps AS "videoFps",job.voice_concurrency AS "voiceConcurrency",job.voice_provider AS "voiceProvider",job.voice_model AS "voiceModel",job.voice_id AS "voiceId",job.narration_speed::float8 AS "narrationSpeed",job.harness_id AS "harnessId",job.harness_version AS "harnessVersion",job.duration_profile AS "durationProfile",job.aspect_ratio AS "aspectRatio",job.subtitles_enabled AS "subtitlesEnabled",episode.ordinal AS "episodeNumber",episode.title AS "episodeTitle",version.status AS "reviewStatus",version.quality_gate_report->>'status' AS "qualityGateStatus" FROM generation_jobs job LEFT JOIN episodes episode ON episode.id=job.episode_id LEFT JOIN production_versions version ON version.id=job.production_version_id WHERE job.id=$1 AND job.user_id=$2`, [id,userId]);
    if (!result.rowCount) throw new NotFoundException();
    const job = result.rows[0];
    const queue = await this.videoQueue.safeSnapshot(id);
    const activeInQueue = queue?.activeJobIds.includes(id) ?? false;
    const effectiveStatus = activeInQueue ? 'running' : job.status;
    const queued = effectiveStatus === 'queued' || effectiveStatus === 'waiting';
    const running = effectiveStatus === 'running';
    return {
      ...job,
      musicSelection: publicMusicSelection(job.musicSelection),
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

  async getThumbnail(id: string, userId: string) {
    const result = await this.db.query(`SELECT 1 FROM generation_jobs WHERE id=$1 AND user_id=$2`, [id, userId]);
    if (!result.rowCount) throw new NotFoundException();
    try { return await openThumbnail(id); } catch { throw new NotFoundException('thumbnail not ready'); }
  }

  async review(id: string, userId: string, verdict: "APPROVED" | "REVISION_REQUIRED", note = "") {
    return this.db.transaction(async (client) => {
      const result = await client.query<{ production_version_id: string; episode_id: string }>(`SELECT production_version_id,episode_id FROM generation_jobs WHERE id=$1 AND user_id=$2 AND status='completed' FOR UPDATE`, [id,userId]);
      const row = result.rows[0];
      if (!row?.production_version_id || !row.episode_id) throw new NotFoundException("review target not ready");
      const versionStatus = verdict === "APPROVED" ? "approved" : "revision_required";
      await client.query(`UPDATE quality_reviews SET status=$2,findings=$3::jsonb,created_at=now() WHERE production_version_id=$1 AND review_type='gold'`, [row.production_version_id,verdict,JSON.stringify(note ? [{ note }] : [])]);
      await client.query(`INSERT INTO approvals(id,production_version_id,gate,status,evidence,approved_by) VALUES($1,$2,'gold',$3,$4::jsonb,$5)
        ON CONFLICT(production_version_id,gate) DO UPDATE SET status=excluded.status,evidence=excluded.evidence,approved_by=excluded.approved_by,created_at=now()`, [randomUUID(),row.production_version_id,verdict,{ note },userId]);
      await client.query(`UPDATE production_versions SET status=$2,updated_at=now() WHERE id=$1`, [row.production_version_id,versionStatus]);
      await client.query(`UPDATE episodes SET status=$2,updated_at=now() WHERE id=$1`, [row.episode_id,versionStatus]);
      await client.query(`UPDATE delivery_receipts SET validation_status=$2,manifest=jsonb_set(manifest,'{humanGoldReview}',to_jsonb($2::text),true) WHERE production_version_id=$1`, [row.production_version_id,verdict]);
      return { id, reviewStatus: versionStatus };
    });
  }
}
