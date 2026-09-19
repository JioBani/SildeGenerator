import { BadRequestException, Body, Controller, Get, GoneException, NotFoundException, Param, ParseIntPipe, ParseUUIDPipe, Post, Put, Query, StreamableFile } from "@nestjs/common";
import { createReadStream } from "node:fs";
import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";
import { Public } from "../auth/public.decorator";
import { DatabaseService } from "../database/database.service";
import { UpdatePromptDto } from "./dto/update-prompt.dto";
import { RestorePromptDto } from "./dto/restore-prompt.dto";
import { UpdateQualityDto } from "./dto/update-quality.dto";
import { PromptsService } from "./prompts.service";
import { AnalyticsService } from "./analytics.service";
import { UpdateCodexSettingsDto } from "./dto/update-codex-settings.dto";
import { CodexSettingsService } from "../settings/codex-settings.service";
import { config } from "../config/app-config";
import { openVideo } from "../jobs/safe-video";
import { VideoJobQueueService } from "../queue/video-job-queue.service";
import { VoiceSettingsService } from "../settings/voice-settings.service";
import { UpdateVoiceSettingsDto } from "./dto/update-voice-settings.dto";

@Public()
@Controller("admin")
export class AdminController {
  constructor(
    private readonly db: DatabaseService,
    private readonly prompts: PromptsService,
    private readonly analytics: AnalyticsService,
    private readonly codexSettings: CodexSettingsService,
    private readonly videoQueue: VideoJobQueueService,
    private readonly voiceSettings: VoiceSettingsService,
  ) {}

  @Get("harnesses")
  async harnesses() {
    const response = await fetch(`${config.runnerUrl}/harnesses`);
    if (!response.ok) throw new BadRequestException("Harness 목록을 불러오지 못했습니다.");
    return response.json();
  }

  @Get("harnesses/:id")
  async harness(@Param("id") id: string) {
    if (!/^[a-z][a-z0-9-]{1,63}$/.test(id)) throw new BadRequestException("Harness ID 형식이 올바르지 않습니다.");
    const response = await fetch(`${config.runnerUrl}/harnesses/${id}`);
    if (!response.ok) throw new NotFoundException("Harness를 찾지 못했습니다.");
    return response.json();
  }

  @Get("settings/voice")
  async getVoiceSettings() { return this.voiceSettings.get(); }

  @Put("settings/voice")
  async updateVoiceSettings(@Body() body: UpdateVoiceSettingsDto) { return this.voiceSettings.update(body); }

  @Get("settings/voice/options")
  async voiceOptions(@Query("provider") provider?: string, @Query("locale") locale = "ko-KR") {
    if (provider !== "microsoft_edge") return { provider, locale, voices: [] };
    return { provider, locale, cached: true, voices: [
      { id: "ko-KR-InJoonNeural", name: "인준 (남성)" },
      { id: "ko-KR-SunHiNeural", name: "선희 (여성)" },
      { id: "ko-KR-HyunsuMultilingualNeural", name: "현수 다국어 (남성)" },
    ] };
  }

  @Post("settings/voice/sample")
  async voiceSample(@Body() body: { text?: string; confirmCredit?: boolean }) {
    const text = String(body.text ?? "안녕하세요. 음성 설정을 확인합니다.").trim();
    if (!text || text.length > 200) throw new BadRequestException("테스트 문장은 1~200자여야 합니다.");
    const voice = await this.voiceSettings.snapshot();
    if (voice.provider === "elevenlabs" && body.confirmCredit !== true) throw new BadRequestException("ElevenLabs credit 사용에 동의해야 테스트할 수 있습니다.");
    const response = await fetch(`${config.runnerUrl}/voice-sample`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ text, voice_settings: {
      provider: voice.provider, model: voice.model, voice_id: voice.voiceId, voice_name: voice.voiceName,
      rate: voice.rate, pitch: voice.pitch, volume: voice.volume, stability: voice.stability,
      similarity_boost: voice.similarityBoost, speed: voice.speed, version: voice.version,
    } }) });
    if (!response.ok) throw new BadRequestException("음성 테스트 생성에 실패했습니다.");
    return new StreamableFile(Buffer.from(await response.arrayBuffer()), { type: "audio/mpeg", disposition: 'inline; filename="voice-sample.mp3"' });
  }

  @Get("codex-settings")
  async getCodexSettings() {
    return this.codexSettings.get();
  }

  @Put("codex-settings")
  async updateCodexSettings(@Body() body: UpdateCodexSettingsDto) {
    return this.codexSettings.update(body);
  }

  @Get("prompts")
  async promptList() {
    return this.prompts.list();
  }

  @Put("prompts/:id")
  async updatePrompt(@Param("id") id: string, @Body() body: UpdatePromptDto) {
    return this.prompts.update(id, body.content, body.expectedSha256);
  }

  @Get("prompts/:id/versions")
  async promptVersions(@Param("id") id: string) {
    return this.prompts.versions(id);
  }

  @Put("prompts/:id/versions/:version/restore")
  async restorePrompt(
    @Param("id") id: string,
    @Param("version") rawVersion: string,
    @Body() body: RestorePromptDto,
  ) {
    const version = Number(rawVersion);
    if (!Number.isSafeInteger(version) || version < 1) return this.prompts.restore(id, -1, body.expectedSha256);
    return this.prompts.restore(id, version, body.expectedSha256);
  }

  @Get("analytics")
  async analyticsComparison(@Query("groupBy") groupBy?: string) {
    return this.analytics.compare(groupBy);
  }

  @Get("dashboard")
  async dashboard() {
    const [jobs, usage, stages, queueWait, queue] = await Promise.all([
      this.db.query(`SELECT count(*)::int AS total,
        count(*) FILTER (WHERE status='completed')::int AS completed,
        count(*) FILTER (WHERE status='failed')::int AS failed,
        count(*) FILTER (WHERE status IN ('queued','running'))::int AS active,
        coalesce(avg(total_duration_ms) FILTER (WHERE status='completed' AND total_duration_ms IS NOT NULL),0)::bigint AS "averageDurationMs"
        FROM generation_jobs`),
      this.db.query(`SELECT coalesce(sum(input_tokens),0)::bigint AS "inputTokens",coalesce(sum(cached_input_tokens),0)::bigint AS "cachedInputTokens",coalesce(sum(output_tokens),0)::bigint AS "outputTokens",coalesce(sum(reasoning_tokens),0)::bigint AS "reasoningTokens",coalesce(sum(characters),0)::bigint AS characters,coalesce(sum(images_generated),0)::bigint AS images,
        coalesce(sum(actual_cost_usd),0)::numeric AS "actualCostUsd",coalesce(sum(api_equivalent_cost_usd),0)::numeric AS "apiEquivalentCostUsd",
        coalesce(sum(actual_cost_usd*exchange_rate_usd_krw),0)::numeric AS "actualCostKrw",coalesce(sum(api_equivalent_cost_usd*exchange_rate_usd_krw),0)::numeric AS "apiEquivalentCostKrw",
        coalesce(sum(api_equivalent_cost_usd*exchange_rate_usd_krw) FILTER (WHERE provider='codex_subscription'),0)::numeric AS "codexApiEquivalentCostKrw",
        coalesce(sum(api_equivalent_cost_usd*exchange_rate_usd_krw) FILTER (WHERE stage IN ('image_generation','keycut_generation','continuity_asset_generation')),0)::numeric AS "imageApiEquivalentCostKrw"
        FROM provider_usage_events`),
      this.db.query(`SELECT stage,count(*)::int AS runs,coalesce(avg(duration_ms),0)::bigint AS "averageDurationMs",coalesce(sum(duration_ms),0)::bigint AS "totalDurationMs" FROM job_stage_runs GROUP BY stage ORDER BY stage`),
      this.db.query(`SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY duration_ms) AS "p50Ms",percentile_cont(0.95) WITHIN GROUP (ORDER BY duration_ms) AS "p95Ms" FROM job_stage_runs WHERE stage IN ('queue_wait','retry_wait') AND status='completed'`),
      this.videoQueue.safeSnapshot(),
    ]);
    return {
      jobs: jobs.rows[0], usage: usage.rows[0], stages: stages.rows,
      queue: {
        activeJobs: queue?.activeJobs ?? null,
        queuedJobs: queue?.queuedJobs ?? null,
        oldestWaitMs: queue?.oldestWaitMs ?? null,
        globalConcurrency: queue?.globalConcurrency ?? config.videoJobGlobalConcurrency,
        queueWaitP50Ms: queueWait.rows[0]?.p50Ms ?? null,
        queueWaitP95Ms: queueWait.rows[0]?.p95Ms ?? null,
      },
    };
  }

  @Get("image-queue")
  async imageQueue() {
    const [summary, attempts, slots, breakdown, referenceDistribution, timeline] = await Promise.all([
      this.db.query(`SELECT
        count(*) FILTER (WHERE status IN ('waiting_dependencies','queued','leased','running','retry_wait'))::int AS "queueDepth",
        count(*) FILTER (WHERE status IN ('leased','running'))::int AS active,
        count(*) FILTER (WHERE status='succeeded')::int AS succeeded,
        count(*) FILTER (WHERE status='failed')::int AS failed,
        count(*) FILTER (WHERE task_type='continuity_asset')::int AS "continuityAssets",
        count(*) FILTER (WHERE task_type='scene' AND jsonb_array_length(reference_asset_ids)=0)::int AS "unreferencedScenes",
        count(*) FILTER (WHERE task_type='scene')::int AS scenes
        FROM image_tasks`),
      this.db.query(`SELECT count(*)::int AS attempts,
        count(*) FILTER (WHERE attempt>1)::int AS retries,
        count(*) FILTER (WHERE status='failed')::int AS "failedAttempts",
        count(*) FILTER (WHERE http_status=429)::int AS "rateLimited",
        max(configured_concurrency)::int AS "configuredConcurrency",
        max(effective_concurrency)::int AS "effectiveConcurrency",
        min(provider_started_at) AS "firstStartedAt",max(finished_at) AS "lastFinishedAt",
        percentile_cont(0.5) WITHIN GROUP (ORDER BY provider_duration_ms) AS "providerP50Ms",
        percentile_cont(0.95) WITHIN GROUP (ORDER BY provider_duration_ms) AS "providerP95Ms",
        percentile_cont(0.5) WITHIN GROUP (ORDER BY queue_wait_ms) AS "queueP50Ms",
        percentile_cont(0.95) WITHIN GROUP (ORDER BY queue_wait_ms) AS "queueP95Ms"
        FROM image_task_attempts`),
      this.db.query(`SELECT slot_id,count(*)::int AS attempts,
        min(provider_started_at) AS "firstStartedAt",max(finished_at) AS "lastFinishedAt",
        coalesce(sum(provider_duration_ms),0)::bigint AS "busyMs"
        FROM image_task_attempts GROUP BY slot_id ORDER BY slot_id`),
      this.db.query(`SELECT task.task_type AS "taskType",count(*)::int AS tasks,
        count(*) FILTER (WHERE task.status='succeeded')::int AS succeeded,
        count(*) FILTER (WHERE task.status='failed')::int AS failed,
        coalesce(sum(attempt.provider_duration_ms),0)::bigint AS "providerMs"
        FROM image_tasks task LEFT JOIN image_task_attempts attempt USING(image_task_id)
        GROUP BY task.task_type ORDER BY task.task_type`),
      this.db.query(`SELECT jsonb_array_length(reference_asset_ids)::int AS "referenceCount",count(*)::int AS scenes
        FROM image_tasks WHERE task_type='scene' GROUP BY 1 ORDER BY 1`),
      this.db.query(`SELECT task.job_id AS "jobId",task.task_type AS "taskType",task.scene_id AS "sceneId",task.asset_id AS "assetId",
        attempt.attempt,attempt.slot_id AS "slotId",attempt.status,attempt.provider_started_at AS "startedAt",
        attempt.finished_at AS "finishedAt",attempt.provider_duration_ms AS "providerMs",attempt.queue_wait_ms AS "queueWaitMs",
        attempt.effective_concurrency AS "effectiveConcurrency",jsonb_array_length(task.reference_asset_ids)::int AS "referenceCount"
        FROM image_task_attempts attempt JOIN image_tasks task USING(image_task_id)
        ORDER BY attempt.provider_started_at DESC NULLS LAST LIMIT 100`),
    ]);
    const attemptSummary = attempts.rows[0];
    const first = attemptSummary.firstStartedAt ? new Date(attemptSummary.firstStartedAt).getTime() : 0;
    const last = attemptSummary.lastFinishedAt ? new Date(attemptSummary.lastFinishedAt).getTime() : 0;
    const minutes = Math.max(0, (last - first) / 60_000);
    return {
      ...summary.rows[0], ...attemptSummary,
      configuredConcurrency: attemptSummary.configuredConcurrency ?? 4,
      imagesPerMinute: minutes > 0 ? Number(summary.rows[0].succeeded) / minutes : null,
      slots: slots.rows,
      breakdown: breakdown.rows,
      referenceDistribution: referenceDistribution.rows,
      timeline: timeline.rows,
    };
  }

  @Get("voice-queue")
  async voiceQueue() {
    const [summary, attempts, slots, timeline] = await Promise.all([
      this.db.query(`SELECT count(*) FILTER (WHERE status IN ('queued','running','retry_wait'))::int AS "queueDepth",count(*) FILTER (WHERE status='running')::int AS active,count(*) FILTER (WHERE status='succeeded')::int AS succeeded,count(*) FILTER (WHERE status='failed')::int AS failed FROM voice_tasks`),
      this.db.query(`SELECT count(*)::int AS attempts,count(*) FILTER (WHERE attempt>1)::int AS retries,count(*) FILTER (WHERE status='failed')::int AS "failedAttempts",count(*) FILTER (WHERE http_status=429)::int AS "rateLimited",max(configured_concurrency)::int AS "configuredConcurrency",percentile_cont(0.5) WITHIN GROUP (ORDER BY provider_duration_ms) AS "providerP50Ms",percentile_cont(0.95) WITHIN GROUP (ORDER BY provider_duration_ms) AS "providerP95Ms",percentile_cont(0.5) WITHIN GROUP (ORDER BY queue_wait_ms) AS "queueP50Ms",percentile_cont(0.95) WITHIN GROUP (ORDER BY queue_wait_ms) AS "queueP95Ms" FROM voice_task_attempts`),
      this.db.query(`SELECT slot_id,count(*)::int AS attempts,coalesce(sum(provider_duration_ms),0)::bigint AS "busyMs" FROM voice_task_attempts GROUP BY slot_id ORDER BY slot_id`),
      this.db.query(`SELECT task.job_id AS "jobId",task.scene_id AS "sceneId",task.settings_hash AS "settingsHash",attempt.attempt,attempt.slot_id AS "slotId",attempt.status,attempt.provider_started_at AS "startedAt",attempt.finished_at AS "finishedAt",attempt.provider_duration_ms AS "providerMs",attempt.queue_wait_ms AS "queueWaitMs" FROM voice_task_attempts attempt JOIN voice_tasks task USING(voice_task_id) ORDER BY attempt.provider_started_at DESC NULLS LAST LIMIT 100`),
    ]);
    return { ...summary.rows[0], ...attempts.rows[0], configuredConcurrency: attempts.rows[0].configuredConcurrency ?? config.voiceConcurrency, slots: slots.rows, timeline: timeline.rows };
  }

  @Get("jobs")
  async jobs(@Query("limit") rawLimit?: string) {
    const limit = Math.min(200, Math.max(1, Number(rawLimit) || 50));
    const [result, queue] = await Promise.all([
      this.db.query(`SELECT job.id,job.user_id AS "userId",job.status,job.current_stage AS "currentStage",job.progress,job.queued_at AS "queuedAt",job.started_at AS "startedAt",job.finished_at AS "finishedAt",job.total_duration_ms AS "totalDurationMs",job.prompt_set_version AS "promptSetVersion",job.quality_score AS "qualityScore",job.image_model AS "imageModel",job.image_style AS "imageStyle",job.continuity_enabled AS "continuityEnabled",job.video_fps AS "videoFps",job.voice_concurrency AS "voiceConcurrency",job.voice_provider AS "voiceProvider",job.voice_model AS "voiceModel",job.voice_id AS "voiceId",job.harness_id AS "harnessId",job.harness_version AS "harnessVersion",job.error_message AS error,
        (SELECT duration_ms FROM job_stage_runs WHERE job_id=job.id AND stage='queue_wait' ORDER BY attempt LIMIT 1) AS "queueWaitMs",
        CASE WHEN video.duration_ms>0 AND job.total_duration_ms IS NOT NULL THEN round(job.total_duration_ms::numeric*60000/video.duration_ms)::bigint END AS "generationTimePerVideoMinuteMs",
        CASE WHEN video.duration_ms>0 THEN usage.total_cost_krw*60000/video.duration_ms END AS "costPerVideoMinuteKrw"
        FROM generation_jobs job
        LEFT JOIN LATERAL (SELECT max(duration_ms) AS duration_ms FROM generated_assets WHERE job_id=job.id AND asset_type='final_video') video ON true
        LEFT JOIN LATERAL (SELECT coalesce(sum(api_equivalent_cost_usd*exchange_rate_usd_krw),0)::numeric AS total_cost_krw FROM provider_usage_events WHERE job_id=job.id) usage ON true
        ORDER BY job.created_at DESC LIMIT $1`, [limit]),
      this.videoQueue.safeSnapshot(),
    ]);
    return result.rows.map((job) => ({
      ...job,
      queuePosition: job.status === 'queued' && queue ? queue.queuedJobIds.indexOf(job.id) + 1 || null : null,
    }));
  }

  @Get("jobs/:id/codex-transcripts")
  async codexTranscripts(@Param("id", ParseUUIDPipe) id: string) {
    await this.requireJob(id);
    const root = this.transcriptRoot(id);
    const entries = await readdir(root, { withFileTypes: true }).catch(() => []);
    const attempts = await Promise.all(entries
      .filter((entry) => entry.isDirectory() && /^attempt-[1-9][0-9]*$/.test(entry.name))
      .map(async (entry) => {
        const attempt = Number(entry.name.slice("attempt-".length));
        const directory = path.join(root, entry.name);
        const raw = await readFile(path.join(directory, "summary.json"), "utf8").catch(() => "{}");
        let summary: Record<string, unknown> = {};
        try { summary = JSON.parse(raw) as Record<string, unknown>; } catch {}
        const files = await Promise.all(["request", "output", "events", "final", "summary"].map(async (part) => {
          const file = path.join(directory, this.transcriptFilename(part));
          const info = await stat(file).catch(() => null);
          return [part, info?.isFile() ? info.size : null] as const;
        }));
        return { attempt, ...summary, files: Object.fromEntries(files) };
      }));
    return { jobId: id, attempts: attempts.sort((left, right) => right.attempt - left.attempt) };
  }

  @Get("jobs/:id/codex-transcripts/:attempt/:part")
  async codexTranscriptFile(
    @Param("id", ParseUUIDPipe) id: string,
    @Param("attempt", ParseIntPipe) attempt: number,
    @Param("part") part: string,
  ) {
    await this.requireJob(id);
    if (attempt < 1 || attempt > 10) throw new NotFoundException();
    const filename = this.transcriptFilename(part);
    const file = path.join(this.transcriptRoot(id), `attempt-${attempt}`, filename);
    const info = await stat(file).catch(() => null);
    if (!info?.isFile()) throw new NotFoundException("Codex 트랜스크립트 파일이 없습니다.");
    const type = filename.endsWith(".json") ? "application/json; charset=utf-8"
      : filename.endsWith(".jsonl") ? "application/x-ndjson; charset=utf-8"
      : "text/plain; charset=utf-8";
    return new StreamableFile(createReadStream(file), { type, disposition: `inline; filename="${filename}"` });
  }

  @Get("jobs/:id/video")
  async jobVideo(@Param("id", ParseUUIDPipe) id: string) {
    const job = await this.db.query(`SELECT status FROM generation_jobs WHERE id=$1`, [id]);
    if (!job.rowCount || job.rows[0].status !== "completed") throw new NotFoundException("video not ready");
    try {
      const { file, size } = await openVideo(id);
      return new StreamableFile(file.createReadStream(), {
        type: "video/mp4",
        length: size,
        disposition: `attachment; filename="slide-${id}.mp4"`,
      });
    } catch {
      throw new GoneException("video expired");
    }
  }

  @Get("jobs/:id")
  async job(@Param("id", ParseUUIDPipe) id: string) {
    const [job, stages, usage, assets, prompts, events, promptSet, imageTasks, imageAttempts, voiceTasks, voiceAttempts, renderSegments] = await Promise.all([
      this.db.query(`SELECT * FROM generation_jobs WHERE id=$1`, [id]),
      this.db.query(`SELECT * FROM job_stage_runs WHERE job_id=$1 ORDER BY started_at,id`, [id]),
      this.db.query(`SELECT * FROM provider_usage_events WHERE job_id=$1 ORDER BY started_at,id`, [id]),
      this.db.query(`SELECT * FROM generated_assets WHERE job_id=$1 ORDER BY id`, [id]),
      this.db.query(`SELECT prompt_name,relative_path,sha256,prompt_version,created_at FROM prompt_snapshots WHERE job_id=$1 ORDER BY relative_path`, [id]),
      this.db.query(`SELECT event_type,payload,created_at FROM job_events WHERE job_id=$1 ORDER BY id`, [id]),
      this.db.query(`SELECT version,fingerprint,manifest,created_at FROM prompt_sets WHERE version=(SELECT prompt_set_version FROM generation_jobs WHERE id=$1)`, [id]),
      this.db.query(`SELECT * FROM image_tasks WHERE job_id=$1 ORDER BY submitted_at,image_task_id`, [id]),
      this.db.query(`SELECT attempt.* FROM image_task_attempts attempt JOIN image_tasks task USING(image_task_id) WHERE task.job_id=$1 ORDER BY attempt.provider_started_at,attempt.id`, [id]),
      this.db.query(`SELECT * FROM voice_tasks WHERE job_id=$1 ORDER BY submitted_at,voice_task_id`, [id]),
      this.db.query(`SELECT attempt.* FROM voice_task_attempts attempt JOIN voice_tasks task USING(voice_task_id) WHERE task.job_id=$1 ORDER BY attempt.provider_started_at,attempt.id`, [id]),
      this.db.query(`SELECT * FROM render_segments WHERE job_id=$1 ORDER BY segment_index`, [id]),
    ]);
    const metrics = job.rows[0]?.status === "completed" ? await this.analytics.jobMetrics(id) : null;
    return { job: job.rows[0] ?? null, metrics, promptSet: promptSet.rows[0] ?? null, stages: stages.rows, usage: usage.rows, assets: assets.rows, prompts: prompts.rows, events: events.rows, imageTasks: imageTasks.rows, imageAttempts: imageAttempts.rows, voiceTasks: voiceTasks.rows, voiceAttempts: voiceAttempts.rows, renderSegments: renderSegments.rows };
  }

  @Put("jobs/:id/quality")
  async updateQuality(@Param("id", ParseUUIDPipe) id: string, @Body() body: UpdateQualityDto) {
    return this.analytics.updateQuality(id, body.score, body.note);
  }

  @Get("models")
  async models() {
    return (await this.db.query(`SELECT provider,model,count(*)::int AS calls,coalesce(sum(input_tokens),0)::bigint AS "inputTokens",coalesce(sum(output_tokens),0)::bigint AS "outputTokens",coalesce(sum(characters),0)::bigint AS characters,coalesce(sum(images_generated),0)::bigint AS images FROM provider_usage_events GROUP BY provider,model ORDER BY provider,model`)).rows;
  }

  private transcriptRoot(jobId: string) {
    return path.join(config.dataDir, "jobs", jobId, "work", "codex");
  }

  private transcriptFilename(part: string) {
    const files: Record<string, string> = {
      request: "request.json",
      output: "output.txt",
      events: "events.jsonl",
      final: "final-response.json",
      summary: "summary.json",
    };
    const filename = files[part];
    if (!filename) throw new NotFoundException();
    return filename;
  }

  private async requireJob(id: string) {
    const result = await this.db.query(`SELECT 1 FROM generation_jobs WHERE id=$1`, [id]);
    if (!result.rowCount) throw new NotFoundException();
  }
}
