import { Injectable } from "@nestjs/common";
import { createHash } from "node:crypto";
import type { PoolClient } from "pg";
import { config } from "../config/app-config";
import { DatabaseService } from "../database/database.service";
import { PROMPT_CATALOG } from "../admin/prompt-catalog";

const ACTIVE_PROMPT_PATHS = new Set(PROMPT_CATALOG.filter((prompt) => prompt.active).map((prompt) => prompt.relativePath));

export type RunnerStage = {
  stage: string; scene_id?: string | null; attempt?: number; status: string;
  started_at: string; finished_at?: string | null; duration_ms?: number | null;
  metadata?: Record<string, unknown>;
};

export type RunnerUsage = {
  provider: string; model: string; stage: string; scene_id?: string | null; request_id?: string | null;
  effort?: string | null;
  input_tokens?: number; cached_input_tokens?: number; output_tokens?: number; reasoning_tokens?: number;
  characters?: number; images_generated?: number; audio_duration_ms?: number;
  started_at: string; finished_at?: string | null; duration_ms?: number | null;
  raw_usage?: Record<string, unknown>;
};

export type RunnerAsset = {
  scene_id?: string | null; asset_type: string; relative_path: string; sha256: string; size_bytes: number;
  duration_ms?: number | null; width?: number | null; height?: number | null; metadata?: Record<string, unknown>;
};

type Price = {
  input?: number; cachedInput?: number; output?: number; character?: number; image?: number;
  textInput?: number; textCachedInput?: number; imageInput?: number; imageCachedInput?: number;
  source: string;
};
const PRICES: Record<string, Price> = {
  "gpt-5.3-codex": { input: 1.75 / 1_000_000, cachedInput: 0.175 / 1_000_000, output: 14 / 1_000_000, source: "https://developers.openai.com/api/docs/models/gpt-5.3-codex" },
  "gpt-5.6-luna": { input: 0.20 / 1_000_000, cachedInput: 0.02 / 1_000_000, output: 1.20 / 1_000_000, source: "https://developers.openai.com/api/docs/models/gpt-5.6-luna" },
  "gpt-5.6-terra": { input: 2 / 1_000_000, cachedInput: 0.20 / 1_000_000, output: 12 / 1_000_000, source: "https://developers.openai.com/api/docs/models/gpt-5.6-terra" },
  "gpt-5.6-sol": { input: 4 / 1_000_000, cachedInput: 0.40 / 1_000_000, output: 20 / 1_000_000, source: "https://developers.openai.com/api/docs/models/gpt-5.6-sol" },
  "gpt-image-2": { textInput: 2.50 / 1_000_000, textCachedInput: 0.625 / 1_000_000, imageInput: 4 / 1_000_000, imageCachedInput: 1 / 1_000_000, output: 15 / 1_000_000, source: "https://developers.openai.com/api/docs/pricing" },
  "gpt-image-2.5-sunburst": { textInput: 5 / 1_000_000, textCachedInput: 1.25 / 1_000_000, imageInput: 8 / 1_000_000, imageCachedInput: 2 / 1_000_000, output: 30 / 1_000_000, source: "https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst" },
  "gpt-image-2.5-flare": { textInput: 5 / 1_000_000, textCachedInput: 1.25 / 1_000_000, imageInput: 8 / 1_000_000, imageCachedInput: 2 / 1_000_000, output: 30 / 1_000_000, source: "https://developers.openai.com/api/docs/models/gpt-image-2.5-flare" },
  "eleven_flash_v2_5": { character: 0.05 / 1_000, source: "https://elevenlabs.io/pricing/api" },
};

const numeric = (value: unknown) => Number(value) || 0;

export function estimateUsageCost(usage: RunnerUsage) {
  const price = PRICES[usage.model];
  if (!price) return { actual: null, equivalent: null, snapshot: { status: "price_unavailable" } };
  if (usage.provider === "codex_subscription" && usage.raw_usage?.status && usage.raw_usage.status !== "completed") {
    return { actual: null, equivalent: null, snapshot: { ...price, status: "usage_unavailable_after_failed_stream" } };
  }
  if (usage.model.startsWith("gpt-image-") && !(usage.input_tokens || usage.cached_input_tokens || usage.output_tokens)) {
    return { actual: null, equivalent: null, snapshot: { ...price, status: "usage_unavailable" } };
  }
  let equivalent: number;
  let tokenBreakdown: Record<string, number> | undefined;
  if (usage.model.startsWith("gpt-image-") && price.textInput !== undefined && price.imageInput !== undefined) {
    const imageUsage = usage.raw_usage?.image as Record<string, unknown> | undefined;
    const details = imageUsage?.input_tokens_details as Record<string, unknown> | undefined;
    const totalInput = numeric(usage.input_tokens);
    let textInput = numeric(details?.text_tokens);
    let imageInput = numeric(details?.image_tokens);
    if (!textInput && !imageInput) textInput = totalInput;
    const detailedTotal = textInput + imageInput;
    const cachedTotal = Math.min(numeric(usage.cached_input_tokens), detailedTotal);
    const cachedText = detailedTotal ? cachedTotal * textInput / detailedTotal : cachedTotal;
    const cachedImage = cachedTotal - cachedText;
    equivalent = (textInput - cachedText) * price.textInput
      + cachedText * (price.textCachedInput ?? price.textInput)
      + (imageInput - cachedImage) * price.imageInput
      + cachedImage * (price.imageCachedInput ?? price.imageInput)
      + numeric(usage.output_tokens) * (price.output ?? 0);
    tokenBreakdown = { textInput, imageInput, cachedText, cachedImage, outputImage: numeric(usage.output_tokens) };
  } else {
    const uncached = Math.max(0, numeric(usage.input_tokens) - numeric(usage.cached_input_tokens));
    equivalent = uncached * (price.input ?? 0)
      + numeric(usage.cached_input_tokens) * (price.cachedInput ?? price.input ?? 0)
      + numeric(usage.output_tokens) * (price.output ?? 0)
      + numeric(usage.characters) * (price.character ?? 0)
      + numeric(usage.images_generated) * (price.image ?? 0);
  }
  return {
    actual: usage.provider === "elevenlabs" ? equivalent : null,
    equivalent,
    snapshot: { ...price, tokenBreakdown, effectiveAt: new Date().toISOString(), currency: "USD" },
  };
}

@Injectable()
export class MetricsService {
  constructor(private readonly db: DatabaseService) {}

  private cost(usage: RunnerUsage) {
    return estimateUsageCost(usage);
  }

  async recordRunnerResult(jobId: string, stages: RunnerStage[], usage: RunnerUsage[], assets: RunnerAsset[], prompts: Array<{ name: string; relative_path: string; sha256: string; content: string }>) {
    await this.db.transaction(async (client) => {
      for (const stage of stages) await this.insertStage(client, jobId, stage);
      for (const event of usage) {
        const price = this.cost(event);
        const effort = event.effort ?? (typeof event.raw_usage?.reasoning_effort === "string" ? event.raw_usage.reasoning_effort : null);
        await client.query(`INSERT INTO provider_usage_events
          (job_id,scene_id,stage,provider,model,request_id,input_tokens,cached_input_tokens,output_tokens,reasoning_tokens,characters,images_generated,audio_duration_ms,started_at,finished_at,duration_ms,actual_cost_usd,api_equivalent_cost_usd,exchange_rate_usd_krw,price_snapshot,raw_usage,effort)
          VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22)`,
          [jobId,event.scene_id ?? null,event.stage,event.provider,event.model,event.request_id ?? null,event.input_tokens ?? 0,event.cached_input_tokens ?? 0,event.output_tokens ?? 0,event.reasoning_tokens ?? 0,event.characters ?? 0,event.images_generated ?? 0,event.audio_duration_ms ?? 0,event.started_at,event.finished_at ?? null,event.duration_ms ?? null,price.actual,price.equivalent,config.usdKrwRate,price.snapshot,event.raw_usage ?? {},effort]);
      }
      for (const asset of assets) await client.query(`INSERT INTO generated_assets
        (job_id,scene_id,asset_type,relative_path,sha256,size_bytes,duration_ms,width,height,metadata)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)`, [jobId,asset.scene_id ?? null,asset.asset_type,asset.relative_path,asset.sha256,asset.size_bytes,asset.duration_ms ?? null,asset.width ?? null,asset.height ?? null,asset.metadata ?? {}]);
      const manifest: Array<{ relativePath: string; version: number; sha256: string }> = [];
      for (const prompt of prompts) {
        const version = await this.ensurePromptVersion(client, prompt.relative_path, prompt.sha256, prompt.content);
        if (ACTIVE_PROMPT_PATHS.has(prompt.relative_path)) manifest.push({ relativePath: prompt.relative_path, version, sha256: prompt.sha256 });
        await client.query(`INSERT INTO prompt_snapshots(job_id,prompt_name,relative_path,sha256,content,prompt_version)
          VALUES ($1,$2,$3,$4,$5,$6)
          ON CONFLICT(job_id,relative_path) DO UPDATE SET prompt_name=excluded.prompt_name,sha256=excluded.sha256,content=excluded.content,prompt_version=excluded.prompt_version`,
          [jobId,prompt.name,prompt.relative_path,prompt.sha256,prompt.content,version]);
      }
      if (manifest.length) {
        manifest.sort((a, b) => a.relativePath.localeCompare(b.relativePath));
        const fingerprint = createHash("sha256").update(JSON.stringify(manifest), "utf8").digest("hex");
        await client.query(`SELECT pg_advisory_xact_lock(hashtext('slidegen_prompt_sets'))`);
        const promptSet = await client.query<{ version: string }>(`INSERT INTO prompt_sets(fingerprint,manifest) VALUES($1,$2)
          ON CONFLICT(fingerprint) DO UPDATE SET fingerprint=excluded.fingerprint RETURNING version`, [fingerprint, JSON.stringify(manifest)]);
        await client.query(`UPDATE generation_jobs SET prompt_set_version=$2 WHERE id=$1`, [jobId, promptSet.rows[0].version]);
      }
    });
  }

  private async ensurePromptVersion(client: PoolClient, relativePath: string, sha256: string, content: string): Promise<number> {
    await client.query(`SELECT pg_advisory_xact_lock(hashtext($1))`, [relativePath]);
    const existing = await client.query<{ version: number }>(`SELECT version FROM prompt_versions WHERE relative_path=$1 AND sha256=$2`, [relativePath, sha256]);
    if (existing.rows[0]) return existing.rows[0].version;
    const inserted = await client.query<{ version: number }>(`INSERT INTO prompt_versions(relative_path,version,sha256,content)
      SELECT $1,coalesce(max(version),0)+1,$2,$3 FROM prompt_versions WHERE relative_path=$1 RETURNING version`, [relativePath, sha256, content]);
    return inserted.rows[0].version;
  }

  private insertStage(client: PoolClient, jobId: string, stage: RunnerStage) {
    return client.query(`INSERT INTO job_stage_runs(job_id,scene_id,stage,attempt,status,started_at,finished_at,duration_ms,metadata)
      VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)`, [jobId,stage.scene_id ?? null,stage.stage,stage.attempt ?? 1,stage.status,stage.started_at,stage.finished_at ?? null,stage.duration_ms ?? null,stage.metadata ?? {}]);
  }
}
