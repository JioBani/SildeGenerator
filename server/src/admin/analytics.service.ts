import { BadRequestException, Injectable, NotFoundException } from "@nestjs/common";
import { DatabaseService } from "../database/database.service";

type GroupBy = "promptVersion" | "model" | "effort" | "imageModel" | "imageStyle" | "imageQuality" | "imageConcurrency" | "referenceCount" | "continuityMode" | "voiceProvider" | "voiceModel" | "voiceConcurrency" | "fps" | "harnessVersion";

type MetricRow = {
  id: string;
  finishedAt: Date;
  totalGenerationTimeMs: string;
  videoDurationMs: string;
  promptSetVersion: string | null;
  qualityScore: string | null;
  qualityNote: string | null;
  model: string | null;
  effort: string | null;
  imageModel: string | null;
  imageStyle: string;
  imageQuality: string | null;
  imageConcurrency: string | null;
  referenceCount: string | null;
  continuityMode: string;
  voiceConcurrency: string;
  voiceProvider: string;
  fps: string;
  voiceModel: string | null;
  harnessVersion: string;
  codexInputTokens: string;
  codexOutputTokens: string;
  codexReasoningTokens: string;
  imageInputTokens: string;
  imageOutputTokens: string;
  imageCount: string;
  voiceCharacters: string;
  voiceDurationMs: string;
  inferenceCostKrw: string;
  imageCostKrw: string;
  imageCostUsd: string;
  exchangeRateUsdKrw: string;
  voiceCostKrw: string;
  totalCostKrw: string;
  actualExternalCostKrw: string;
  unpricedEvents: string;
};

type NormalizedMetric = ReturnType<AnalyticsService["normalize"]>;

const number = (value: unknown) => Number(value) || 0;
const divide = (numerator: number, denominator: number) => denominator > 0 ? numerator / denominator : null;

@Injectable()
export class AnalyticsService {
  constructor(private readonly db: DatabaseService) {}

  private async metricRows(jobId?: string): Promise<MetricRow[]> {
    const result = await this.db.query<MetricRow>(`SELECT
      job.id,job.finished_at AS "finishedAt",coalesce(job.total_duration_ms,0)::bigint AS "totalGenerationTimeMs",
      coalesce(asset.video_duration_ms,0)::bigint AS "videoDurationMs",job.prompt_set_version::text AS "promptSetVersion",
      job.quality_score::text AS "qualityScore",job.quality_note AS "qualityNote",planning.model,planning.effort,
      coalesce(image_config.image_model,usage.image_model) AS "imageModel",job.image_style AS "imageStyle",
      image_config.image_quality AS "imageQuality",
      image_config.image_concurrency::text AS "imageConcurrency",
      image_config.reference_count::text AS "referenceCount",
      CASE WHEN job.continuity_enabled THEN 'ON' ELSE 'OFF' END AS "continuityMode",
      job.voice_concurrency::text AS "voiceConcurrency",job.video_fps::text AS fps,
      job.voice_provider AS "voiceProvider",coalesce(job.voice_model,usage.voice_model) AS "voiceModel",job.harness_id||'@'||job.harness_version AS "harnessVersion",
      coalesce(usage.codex_input_tokens,0)::bigint AS "codexInputTokens",
      coalesce(usage.codex_output_tokens,0)::bigint AS "codexOutputTokens",
      coalesce(usage.codex_reasoning_tokens,0)::bigint AS "codexReasoningTokens",
      coalesce(usage.image_input_tokens,0)::bigint AS "imageInputTokens",
      coalesce(usage.image_output_tokens,0)::bigint AS "imageOutputTokens",
      coalesce(usage.image_count,0)::bigint AS "imageCount",
      coalesce(usage.voice_characters,0)::bigint AS "voiceCharacters",
      coalesce(usage.voice_duration_ms,0)::bigint AS "voiceDurationMs",
      coalesce(usage.inference_cost_krw,0)::numeric AS "inferenceCostKrw",
      coalesce(usage.image_cost_krw,0)::numeric AS "imageCostKrw",
      coalesce(usage.image_cost_usd,0)::numeric AS "imageCostUsd",
      coalesce(usage.exchange_rate_usd_krw,0)::numeric AS "exchangeRateUsdKrw",
      coalesce(usage.voice_cost_krw,0)::numeric AS "voiceCostKrw",
      coalesce(usage.total_cost_krw,0)::numeric AS "totalCostKrw",
      coalesce(usage.actual_external_cost_krw,0)::numeric AS "actualExternalCostKrw",
      coalesce(usage.unpriced_events,0)::bigint AS "unpricedEvents"
      FROM generation_jobs job
      LEFT JOIN LATERAL (
        SELECT max(duration_ms) FILTER (WHERE asset_type='final_video') AS video_duration_ms
        FROM generated_assets WHERE job_id=job.id
      ) asset ON true
      LEFT JOIN LATERAL (
        SELECT model,coalesce(effort,raw_usage->>'reasoning_effort','미기록') AS effort
        FROM provider_usage_events WHERE job_id=job.id AND stage='scene_planning'
        ORDER BY id DESC LIMIT 1
      ) planning ON true
      LEFT JOIN LATERAL (
        SELECT max(task.model) AS image_model,max(task.quality) AS image_quality,
          max(attempt.configured_concurrency) AS image_concurrency,
          max(jsonb_array_length(task.reference_asset_ids)) AS reference_count
        FROM image_tasks task
        LEFT JOIN image_task_attempts attempt ON attempt.image_task_id=task.image_task_id
        WHERE task.job_id=job.id
      ) image_config ON true
      LEFT JOIN LATERAL (
        SELECT
          sum(input_tokens) FILTER (WHERE provider='codex_subscription') AS codex_input_tokens,
          sum(output_tokens) FILTER (WHERE provider='codex_subscription') AS codex_output_tokens,
          sum(reasoning_tokens) FILTER (WHERE provider='codex_subscription') AS codex_reasoning_tokens,
          sum(input_tokens) FILTER (WHERE stage IN ('image_generation','keycut_generation','continuity_asset_generation')) AS image_input_tokens,
          sum(output_tokens) FILTER (WHERE stage IN ('image_generation','keycut_generation','continuity_asset_generation')) AS image_output_tokens,
          sum(images_generated) FILTER (WHERE stage IN ('image_generation','keycut_generation','continuity_asset_generation')) AS image_count,
          sum(characters) FILTER (WHERE provider IN ('elevenlabs','microsoft_edge_tts','mock')) AS voice_characters,
          sum(audio_duration_ms) FILTER (WHERE provider IN ('elevenlabs','microsoft_edge_tts','mock')) AS voice_duration_ms,
          max(model) FILTER (WHERE stage IN ('image_generation','keycut_generation','continuity_asset_generation')) AS image_model,
          max(model) FILTER (WHERE provider='elevenlabs') AS voice_model,
          sum(api_equivalent_cost_usd*exchange_rate_usd_krw) FILTER (WHERE provider='codex_subscription') AS inference_cost_krw,
          sum(api_equivalent_cost_usd*exchange_rate_usd_krw) FILTER (WHERE stage IN ('image_generation','keycut_generation','continuity_asset_generation')) AS image_cost_krw,
          sum(api_equivalent_cost_usd) FILTER (WHERE stage IN ('image_generation','keycut_generation','continuity_asset_generation')) AS image_cost_usd,
          max(exchange_rate_usd_krw) FILTER (WHERE stage IN ('image_generation','keycut_generation','continuity_asset_generation')) AS exchange_rate_usd_krw,
          sum(api_equivalent_cost_usd*exchange_rate_usd_krw) FILTER (WHERE provider='elevenlabs') AS voice_cost_krw,
          sum(api_equivalent_cost_usd*exchange_rate_usd_krw) AS total_cost_krw,
          sum(actual_cost_usd*exchange_rate_usd_krw) AS actual_external_cost_krw,
          count(*) FILTER (WHERE provider<>'mock' AND api_equivalent_cost_usd IS NULL) AS unpriced_events
        FROM provider_usage_events WHERE job_id=job.id
      ) usage ON true
      WHERE job.status='completed' AND ($1::uuid IS NULL OR job.id=$1)
        AND ($1::uuid IS NOT NULL OR EXISTS (SELECT 1 FROM provider_usage_events live_usage WHERE live_usage.job_id=job.id AND live_usage.provider<>'mock'))
      ORDER BY job.finished_at`, [jobId ?? null]);
    return result.rows;
  }

  private normalize(row: MetricRow) {
    const videoDurationMs = number(row.videoDurationMs);
    const voiceDurationMs = number(row.voiceDurationMs);
    const imageCount = number(row.imageCount);
    const videoMinutes = videoDurationMs / 60_000;
    const voiceMinutes = voiceDurationMs / 60_000;
    const inferenceCostKrw = number(row.inferenceCostKrw);
    const imageCostKrw = number(row.imageCostKrw);
    const voiceCostKrw = number(row.voiceCostKrw);
    const totalCostKrw = number(row.totalCostKrw);
    return {
      jobId: row.id,
      finishedAt: row.finishedAt,
      totalGenerationTimeMs: number(row.totalGenerationTimeMs),
      videoDurationMs,
      promptSetVersion: row.promptSetVersion ? number(row.promptSetVersion) : null,
      model: row.model ?? "미기록",
      effort: row.effort ?? "미기록",
      imageModel: row.imageModel ?? "미기록",
      imageStyle: row.imageStyle ?? "legacy",
      imageQuality: row.imageQuality ?? "미기록",
      imageConcurrency: row.imageConcurrency === null ? "미기록" : String(number(row.imageConcurrency)),
      referenceCount: row.referenceCount === null ? "미기록" : String(number(row.referenceCount)),
      continuityMode: row.continuityMode,
      voiceConcurrency: row.voiceConcurrency,
      voiceProvider: row.voiceProvider ?? "legacy",
      fps: row.fps,
      voiceModel: row.voiceModel ?? "미기록",
      harnessVersion: row.harnessVersion ?? "classic-slide@legacy",
      qualityScore: row.qualityScore === null ? null : number(row.qualityScore),
      qualityNote: row.qualityNote,
      codexInputTokens: number(row.codexInputTokens),
      codexOutputTokens: number(row.codexOutputTokens),
      codexReasoningTokens: number(row.codexReasoningTokens),
      imageInputTokens: number(row.imageInputTokens),
      imageOutputTokens: number(row.imageOutputTokens),
      imageTokens: number(row.imageInputTokens) + number(row.imageOutputTokens),
      imageCount,
      voiceCharacters: number(row.voiceCharacters),
      voiceDurationMs,
      inferenceCostKrw,
      imageCostKrw,
      imageApiEstimatedCostKrw: imageCostKrw,
      imageApiEstimatedCostUsd: number(row.imageCostUsd),
      imageApiExchangeRateUsdKrw: number(row.exchangeRateUsdKrw),
      voiceCostKrw,
      actualExternalCostKrw: number(row.actualExternalCostKrw),
      unpricedEvents: number(row.unpricedEvents),
      costComplete: number(row.unpricedEvents) === 0,
      totalCostKrw,
      inferenceCostPerVideoMinuteKrw: divide(inferenceCostKrw, videoMinutes),
      imageCostPerImageKrw: divide(imageCostKrw, imageCount),
      voiceCostPerMinuteKrw: divide(voiceCostKrw, voiceMinutes),
      totalCostPerVideoMinuteKrw: divide(totalCostKrw, videoMinutes),
    };
  }

  async jobMetrics(jobId: string) {
    const [row] = await this.metricRows(jobId);
    if (!row) throw new NotFoundException("완료된 작업의 측정값을 찾을 수 없습니다.");
    const stages = await this.db.query(`SELECT stage,count(*)::int AS runs,
      coalesce((extract(epoch FROM (max(coalesce(finished_at,started_at))-min(started_at)))*1000)::bigint,0) AS "wallClockDurationMs",
      coalesce(sum(duration_ms),0)::bigint AS "totalDurationMs",coalesce(avg(duration_ms),0)::bigint AS "averageDurationMs"
      FROM job_stage_runs WHERE job_id=$1 GROUP BY stage ORDER BY min(started_at)`, [jobId]);
    return { ...this.normalize(row), stages: stages.rows };
  }

  async compare(rawGroupBy?: string) {
    const groupBy = (rawGroupBy ?? "promptVersion") as GroupBy;
    if (!["promptVersion", "model", "effort", "imageModel", "imageStyle", "imageQuality", "imageConcurrency", "referenceCount", "continuityMode", "voiceProvider", "voiceModel", "voiceConcurrency", "fps", "harnessVersion"].includes(groupBy)) {
      throw new BadRequestException("지원하지 않는 groupBy입니다.");
    }
    const metrics = (await this.metricRows()).map((row) => this.normalize(row));
    const groups = new Map<string, NormalizedMetric[]>();
    for (const metric of metrics) {
      const key = groupBy === "promptVersion"
        ? (metric.promptSetVersion ? `v${metric.promptSetVersion}` : "미기록")
        : String(metric[groupBy] ?? "미기록");
      groups.set(key, [...(groups.get(key) ?? []), metric]);
    }
    const average = (items: NormalizedMetric[], select: (item: NormalizedMetric) => number | null) => {
      const values = items.map(select).filter((value): value is number => value !== null && Number.isFinite(value));
      return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
    };
    const sum = (items: NormalizedMetric[], select: (item: NormalizedMetric) => number) => items.reduce((total, item) => total + select(item), 0);
    const rows = Array.from(groups, ([key, items]) => ({
      key,
      jobs: items.length,
      scoredJobs: items.filter((item) => item.qualityScore !== null).length,
      incompleteCostJobs: items.filter((item) => !item.costComplete).length,
      averageQualityScore: average(items, (item) => item.qualityScore),
      averageGenerationTimeMs: average(items, (item) => item.totalGenerationTimeMs),
      averageVideoDurationMs: average(items, (item) => item.videoDurationMs),
      averageCodexReasoningTokens: average(items, (item) => item.codexReasoningTokens),
      averageImageTokensPerImage: divide(sum(items, (item) => item.imageTokens), sum(items, (item) => item.imageCount)),
      averageImageApiCostPerVideoKrw: average(items, (item) => item.imageApiEstimatedCostKrw),
      inferenceCostPerVideoMinuteKrw: divide(sum(items, (item) => item.inferenceCostKrw), sum(items, (item) => item.videoDurationMs) / 60_000),
      imageCostPerImageKrw: divide(sum(items, (item) => item.imageCostKrw), sum(items, (item) => item.imageCount)),
      voiceCostPerMinuteKrw: divide(sum(items, (item) => item.voiceCostKrw), sum(items, (item) => item.voiceDurationMs) / 60_000),
      totalCostPerVideoMinuteKrw: divide(sum(items, (item) => item.totalCostKrw), sum(items, (item) => item.videoDurationMs) / 60_000),
    }));
    rows.sort((a, b) => groupBy === "promptVersion"
      ? number(a.key.replace(/^v/, "")) - number(b.key.replace(/^v/, ""))
      : a.key.localeCompare(b.key, "ko"));
    return {
      groupBy,
      rows,
      dimensions: {
        promptVersions: Array.from(new Set(metrics.map((item) => item.promptSetVersion).filter(Boolean))).sort((a, b) => number(a) - number(b)),
        models: Array.from(new Set(metrics.map((item) => item.model))).filter((value) => value !== "미기록").sort(),
        efforts: Array.from(new Set(metrics.map((item) => item.effort))).filter((value) => value !== "미기록").sort(),
        imageModels: Array.from(new Set(metrics.map((item) => item.imageModel))).filter((value) => value !== "미기록").sort(),
        imageStyles: Array.from(new Set(metrics.map((item) => item.imageStyle))).sort(),
        imageQualities: Array.from(new Set(metrics.map((item) => item.imageQuality))).filter((value) => value !== "미기록").sort(),
        imageConcurrencies: Array.from(new Set(metrics.map((item) => item.imageConcurrency))).filter((value) => value !== "미기록").sort((a, b) => number(a) - number(b)),
        referenceCounts: Array.from(new Set(metrics.map((item) => item.referenceCount))).filter((value) => value !== "미기록").sort((a, b) => number(a) - number(b)),
        continuityModes: Array.from(new Set(metrics.map((item) => item.continuityMode))).sort(),
        voiceProviders: Array.from(new Set(metrics.map((item) => item.voiceProvider))).sort(),
        voiceModels: Array.from(new Set(metrics.map((item) => item.voiceModel))).filter((value) => value !== "미기록").sort(),
        voiceConcurrencies: Array.from(new Set(metrics.map((item) => item.voiceConcurrency))).sort((a, b) => number(a) - number(b)),
        fpsValues: Array.from(new Set(metrics.map((item) => item.fps))).sort((a, b) => number(a) - number(b)),
        harnessVersions: Array.from(new Set(metrics.map((item) => item.harnessVersion))).sort(),
      },
    };
  }

  async updateQuality(jobId: string, score: number, note?: string) {
    const result = await this.db.query(`UPDATE generation_jobs SET quality_score=$2,quality_note=$3,updated_at=now()
      WHERE id=$1 AND status='completed' RETURNING id,quality_score AS "qualityScore",quality_note AS "qualityNote"`,
      [jobId, score, note?.trim() || null]);
    if (!result.rows[0]) throw new NotFoundException("완료된 작업을 찾을 수 없습니다.");
    return result.rows[0];
  }
}
