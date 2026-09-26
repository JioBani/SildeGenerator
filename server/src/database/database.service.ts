import { Injectable, Logger, OnModuleDestroy, OnModuleInit } from "@nestjs/common";
import { createHash } from "node:crypto";
import { Pool, type PoolClient, type QueryResultRow } from "pg";
import { config } from "../config/app-config";
import { PROMPT_CATALOG } from "../admin/prompt-catalog";

const ACTIVE_PROMPT_PATHS = PROMPT_CATALOG.filter((prompt) => prompt.active).map((prompt) => prompt.relativePath);

const migrations = [
  `CREATE TABLE IF NOT EXISTS generation_jobs (
    id uuid PRIMARY KEY,
    user_id text NOT NULL,
    title text,
    scenario text NOT NULL,
    status text NOT NULL,
    current_stage text,
    progress integer NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    error_code text,
    error_message text,
    queued_at timestamptz NOT NULL DEFAULT now(),
    started_at timestamptz,
    finished_at timestamptz,
    total_duration_ms bigint,
    output_path text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
  )`,
  `CREATE TABLE IF NOT EXISTS job_stage_runs (
    id bigserial PRIMARY KEY,
    job_id uuid NOT NULL REFERENCES generation_jobs(id) ON DELETE CASCADE,
    scene_id text,
    stage text NOT NULL,
    attempt integer NOT NULL DEFAULT 1,
    status text NOT NULL,
    started_at timestamptz NOT NULL,
    finished_at timestamptz,
    duration_ms bigint,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
  )`,
  `CREATE INDEX IF NOT EXISTS job_stage_runs_job_idx ON job_stage_runs(job_id, started_at)`,
  `CREATE TABLE IF NOT EXISTS provider_usage_events (
    id bigserial PRIMARY KEY,
    job_id uuid NOT NULL REFERENCES generation_jobs(id) ON DELETE CASCADE,
    scene_id text,
    stage text NOT NULL,
    provider text NOT NULL,
    model text NOT NULL,
    request_id text,
    input_tokens bigint NOT NULL DEFAULT 0,
    cached_input_tokens bigint NOT NULL DEFAULT 0,
    output_tokens bigint NOT NULL DEFAULT 0,
    reasoning_tokens bigint NOT NULL DEFAULT 0,
    characters bigint NOT NULL DEFAULT 0,
    images_generated integer NOT NULL DEFAULT 0,
    audio_duration_ms bigint NOT NULL DEFAULT 0,
    started_at timestamptz NOT NULL,
    finished_at timestamptz,
    duration_ms bigint,
    actual_cost_usd numeric(18,8),
    api_equivalent_cost_usd numeric(18,8),
    exchange_rate_usd_krw numeric(18,6) NOT NULL,
    price_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
    raw_usage jsonb NOT NULL DEFAULT '{}'::jsonb
  )`,
  `CREATE INDEX IF NOT EXISTS provider_usage_job_idx ON provider_usage_events(job_id, started_at)`,
  `CREATE TABLE IF NOT EXISTS prompt_snapshots (
    id bigserial PRIMARY KEY,
    job_id uuid NOT NULL REFERENCES generation_jobs(id) ON DELETE CASCADE,
    prompt_name text NOT NULL,
    relative_path text NOT NULL,
    sha256 text NOT NULL,
    content text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(job_id, relative_path)
  )`,
  `CREATE TABLE IF NOT EXISTS generated_assets (
    id bigserial PRIMARY KEY,
    job_id uuid NOT NULL REFERENCES generation_jobs(id) ON DELETE CASCADE,
    scene_id text,
    asset_type text NOT NULL,
    relative_path text NOT NULL,
    sha256 text NOT NULL,
    size_bytes bigint NOT NULL,
    duration_ms bigint,
    width integer,
    height integer,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
  )`,
  `CREATE TABLE IF NOT EXISTS job_events (
    id bigserial PRIMARY KEY,
    job_id uuid NOT NULL REFERENCES generation_jobs(id) ON DELETE CASCADE,
    event_type text NOT NULL,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
  )`,
  `CREATE TABLE IF NOT EXISTS prompt_versions (
    relative_path text NOT NULL,
    version integer NOT NULL,
    sha256 text NOT NULL,
    content text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY(relative_path, version),
    UNIQUE(relative_path, sha256)
  )`,
  `CREATE TABLE IF NOT EXISTS prompt_sets (
    version bigserial PRIMARY KEY,
    fingerprint text NOT NULL UNIQUE,
    manifest jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
  )`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS prompt_set_version bigint REFERENCES prompt_sets(version)`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS quality_score numeric(5,2) CHECK (quality_score >= 0 AND quality_score <= 100)`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS quality_note text`,
  `ALTER TABLE prompt_snapshots ADD COLUMN IF NOT EXISTS prompt_version integer`,
  `ALTER TABLE provider_usage_events ADD COLUMN IF NOT EXISTS effort text`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS codex_model text`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS codex_effort text`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS codex_fast_mode boolean`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS image_model text`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS continuity_enabled boolean NOT NULL DEFAULT false`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS image_style text NOT NULL DEFAULT 'legacy'`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS motion_style jsonb`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS narrative_blueprint jsonb`,
  `DO $$ BEGIN
    ALTER TABLE generation_jobs DROP CONSTRAINT IF EXISTS generation_jobs_image_style_check;
    ALTER TABLE generation_jobs ADD CONSTRAINT generation_jobs_image_style_check
      CHECK (image_style IN ('legacy','editorial_illustration','cinematic_realism','graphic_explainer','cute_character','fantasy_anime','animation_3d','disney_animation','dystopian'));
  END $$`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS video_fps integer NOT NULL DEFAULT 24`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS voice_concurrency integer NOT NULL DEFAULT 2`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS voice_provider text NOT NULL DEFAULT 'legacy'`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS voice_model text`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS voice_id text`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS voice_settings jsonb NOT NULL DEFAULT '{}'::jsonb`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS voice_settings_version bigint NOT NULL DEFAULT 1`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS narration_speed numeric(4,2) NOT NULL DEFAULT 0.7`,
  `ALTER TABLE generation_jobs ALTER COLUMN narration_speed SET DEFAULT 0.7`,
  `DO $$ BEGIN
    IF NOT EXISTS (
      SELECT 1 FROM pg_constraint
      WHERE conname='generation_jobs_narration_speed_check'
        AND pg_get_constraintdef(oid) LIKE '%0.7%'
    ) THEN
      ALTER TABLE generation_jobs DROP CONSTRAINT IF EXISTS generation_jobs_narration_speed_check;
      ALTER TABLE generation_jobs ADD CONSTRAINT generation_jobs_narration_speed_check
        CHECK (narration_speed BETWEEN 0.7 AND 1.5) NOT VALID;
    END IF;
  END $$`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS harness_id text NOT NULL DEFAULT 'classic-slide'`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS harness_version text NOT NULL DEFAULT 'legacy'`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS harness_manifest_sha256 text`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS harness_source_sha256 text`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS harness_config_sha256 text`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS harness_source_revision text`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS harness_image_digest text`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS harness_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb`,
  `UPDATE generation_jobs SET video_fps=30,voice_concurrency=1
    WHERE created_at < TIMESTAMPTZ '2026-09-19 13:26:27+00'
      AND video_fps=24 AND voice_concurrency=2`,
  `DO $$ BEGIN
    ALTER TABLE generation_jobs ADD CONSTRAINT generation_jobs_image_model_check
      CHECK (image_model IS NULL OR image_model IN ('gpt-image-2','gpt-image-2.5-sunburst','gpt-image-2.5-flare'));
    EXCEPTION WHEN duplicate_object THEN NULL;
  END $$`,
  `CREATE TABLE IF NOT EXISTS runtime_settings (
    key text PRIMARY KEY,
    value jsonb NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
  )`,
  `UPDATE provider_usage_events SET effort=raw_usage->>'reasoning_effort' WHERE effort IS NULL AND raw_usage ? 'reasoning_effort'`,
  `CREATE INDEX IF NOT EXISTS generation_jobs_prompt_set_idx ON generation_jobs(prompt_set_version)`,
  `CREATE INDEX IF NOT EXISTS provider_usage_model_effort_idx ON provider_usage_events(model, effort)`,
  `CREATE TABLE IF NOT EXISTS image_tasks (
    image_task_id uuid PRIMARY KEY,
    job_id uuid NOT NULL REFERENCES generation_jobs(id) ON DELETE CASCADE,
    task_type text NOT NULL CHECK (task_type IN ('continuity_asset','scene','manual_regeneration','recovery')),
    scene_id text,
    asset_id text,
    status text NOT NULL CHECK (status IN ('waiting_dependencies','queued','leased','running','retry_wait','succeeded','failed','cancelled')),
    provider text NOT NULL,
    model text NOT NULL,
    quality text NOT NULL,
    size text NOT NULL,
    input_fidelity text,
    prompt_path text NOT NULL,
    prompt_sha256 text NOT NULL,
    prompt_bundle jsonb NOT NULL DEFAULT '{}'::jsonb,
    reference_asset_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
    reference_files jsonb NOT NULL DEFAULT '[]'::jsonb,
    dependency_task_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
    output_path text,
    output_sha256 text,
    output_bytes bigint,
    width integer,
    height integer,
    submitted_at timestamptz NOT NULL DEFAULT now(),
    dependency_ready_at timestamptz,
    queued_at timestamptz,
    leased_at timestamptz,
    started_at timestamptz,
    finished_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT now(),
    error_code text,
    error_message text
  )`,
  `CREATE INDEX IF NOT EXISTS image_tasks_job_status_idx ON image_tasks(job_id,status,submitted_at)`,
  `ALTER TABLE image_tasks DROP CONSTRAINT IF EXISTS image_tasks_task_type_check`,
  `ALTER TABLE image_tasks ADD CONSTRAINT image_tasks_task_type_check CHECK (task_type IN ('continuity_asset','keycut','scene','manual_regeneration','recovery'))`,
  `ALTER TABLE image_tasks ADD COLUMN IF NOT EXISTS priority integer NOT NULL DEFAULT 0`,
  `ALTER TABLE image_tasks ADD COLUMN IF NOT EXISTS parent_keycut_task_id uuid REFERENCES image_tasks(image_task_id)`,
  `ALTER TABLE image_tasks ADD COLUMN IF NOT EXISTS reference_kinds jsonb NOT NULL DEFAULT '[]'::jsonb`,
  `ALTER TABLE image_tasks ADD COLUMN IF NOT EXISTS image_style text`,
  `CREATE TABLE IF NOT EXISTS image_task_attempts (
    id bigserial PRIMARY KEY,
    image_task_id uuid NOT NULL REFERENCES image_tasks(image_task_id) ON DELETE CASCADE,
    attempt integer NOT NULL,
    status text NOT NULL,
    slot_id text,
    active_calls integer,
    configured_concurrency integer,
    effective_concurrency integer,
    queue_depth integer,
    dependency_wait_ms bigint,
    queue_wait_ms bigint,
    provider_duration_ms bigint,
    postprocess_ms bigint,
    total_duration_ms bigint,
    provider_request_id text,
    http_status integer,
    error_code text,
    error_message text,
    retry_backoff_ms bigint,
    potential_duplicate_cost boolean NOT NULL DEFAULT false,
    usage jsonb NOT NULL DEFAULT '{}'::jsonb,
    price_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
    reference_snapshot jsonb NOT NULL DEFAULT '[]'::jsonb,
    submitted_at timestamptz NOT NULL,
    dependency_ready_at timestamptz,
    queued_at timestamptz,
    leased_at timestamptz,
    provider_started_at timestamptz,
    response_received_at timestamptz,
    persisted_at timestamptz,
    finished_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(image_task_id,attempt)
  )`,
  `UPDATE provider_usage_events event SET
    api_equivalent_cost_usd =
      coalesce((event.raw_usage #>> '{image,input_tokens_details,text_tokens}')::numeric,event.input_tokens::numeric)
        * (greatest(event.input_tokens-event.cached_input_tokens,0)::numeric/greatest(event.input_tokens,1)) * price.text_input
      + coalesce((event.raw_usage #>> '{image,input_tokens_details,text_tokens}')::numeric,event.input_tokens::numeric)
        * (event.cached_input_tokens::numeric/greatest(event.input_tokens,1)) * price.text_cached
      + coalesce((event.raw_usage #>> '{image,input_tokens_details,image_tokens}')::numeric,0)
        * (greatest(event.input_tokens-event.cached_input_tokens,0)::numeric/greatest(event.input_tokens,1)) * price.image_input
      + coalesce((event.raw_usage #>> '{image,input_tokens_details,image_tokens}')::numeric,0)
        * (event.cached_input_tokens::numeric/greatest(event.input_tokens,1)) * price.image_cached
      + event.output_tokens * price.image_output,
    price_snapshot = jsonb_build_object(
      'textInput',price.text_input,'textCachedInput',price.text_cached,
      'imageInput',price.image_input,'imageCachedInput',price.image_cached,
      'output',price.image_output,'currency','USD','source',price.source,
      'status','historical_image_cost_recalculated'
    )
    FROM (VALUES
      ('gpt-image-2',0.0000025::numeric,0.000000625::numeric,0.000004::numeric,0.000001::numeric,0.000015::numeric,'https://developers.openai.com/api/docs/pricing'),
      ('gpt-image-2.5-sunburst',0.000005::numeric,0.00000125::numeric,0.000008::numeric,0.000002::numeric,0.000030::numeric,'https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst'),
      ('gpt-image-2.5-flare',0.000005::numeric,0.00000125::numeric,0.000008::numeric,0.000002::numeric,0.000030::numeric,'https://developers.openai.com/api/docs/models/gpt-image-2.5-flare')
    ) AS price(model,text_input,text_cached,image_input,image_cached,image_output,source)
    WHERE event.model=price.model AND event.stage IN ('image_generation','continuity_asset_generation')`,
  `CREATE INDEX IF NOT EXISTS image_task_attempts_timeline_idx ON image_task_attempts(provider_started_at,finished_at)`,
  `CREATE TABLE IF NOT EXISTS voice_tasks (
    voice_task_id uuid PRIMARY KEY,
    job_id uuid NOT NULL REFERENCES generation_jobs(id) ON DELETE CASCADE,
    scene_id text NOT NULL,
    status text NOT NULL CHECK (status IN ('queued','running','retry_wait','succeeded','failed','cancelled')),
    provider text NOT NULL,
    model text NOT NULL,
    settings_hash text NOT NULL,
    settings_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
    narration_sha256 text NOT NULL,
    output_path text,
    output_sha256 text,
    output_bytes bigint,
    qc jsonb NOT NULL DEFAULT '{}'::jsonb,
    submitted_at timestamptz NOT NULL DEFAULT now(),
    queued_at timestamptz NOT NULL DEFAULT now(),
    leased_at timestamptz,
    started_at timestamptz,
    finished_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT now(),
    error_code text,
    error_message text
  )`,
  `CREATE INDEX IF NOT EXISTS voice_tasks_job_status_idx ON voice_tasks(job_id,status,submitted_at)`,
  `CREATE TABLE IF NOT EXISTS voice_task_attempts (
    id bigserial PRIMARY KEY,
    voice_task_id uuid NOT NULL REFERENCES voice_tasks(voice_task_id) ON DELETE CASCADE,
    attempt integer NOT NULL,
    status text NOT NULL,
    slot_id text,
    active_calls integer,
    configured_concurrency integer,
    queue_wait_ms bigint,
    provider_duration_ms bigint,
    total_duration_ms bigint,
    http_status integer,
    error_code text,
    error_message text,
    retry_backoff_ms bigint,
    potential_duplicate_cost boolean NOT NULL DEFAULT false,
    usage jsonb NOT NULL DEFAULT '{}'::jsonb,
    submitted_at timestamptz NOT NULL,
    queued_at timestamptz,
    leased_at timestamptz,
    provider_started_at timestamptz,
    response_received_at timestamptz,
    persisted_at timestamptz,
    finished_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(voice_task_id,attempt)
  )`,
  `CREATE INDEX IF NOT EXISTS voice_task_attempts_timeline_idx ON voice_task_attempts(provider_started_at,finished_at)`,
  `CREATE TABLE IF NOT EXISTS render_segments (
    id bigserial PRIMARY KEY,
    job_id uuid NOT NULL REFERENCES generation_jobs(id) ON DELETE CASCADE,
    segment_index integer NOT NULL,
    first_scene_id text NOT NULL,
    last_scene_id text NOT NULL,
    input_hash text NOT NULL,
    output_path text NOT NULL,
    status text NOT NULL,
    ready_at timestamptz,
    started_at timestamptz,
    finished_at timestamptz,
    duration_ms bigint,
    settings jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE(job_id,segment_index)
  )`,
  `CREATE INDEX IF NOT EXISTS render_segments_job_idx ON render_segments(job_id,segment_index)`,
  `CREATE TABLE IF NOT EXISTS video_projects (
    id uuid PRIMARY KEY,
    user_id text NOT NULL,
    title text NOT NULL,
    status text NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
  )`,
  `CREATE TABLE IF NOT EXISTS episodes (
    id uuid PRIMARY KEY,
    project_id uuid NOT NULL REFERENCES video_projects(id) ON DELETE CASCADE,
    ordinal integer NOT NULL CHECK (ordinal > 0),
    title text NOT NULL,
    status text NOT NULL DEFAULT 'production_requested',
    duration_profile text NOT NULL DEFAULT 'episode_60',
    target_seconds integer NOT NULL DEFAULT 50,
    maximum_seconds integer NOT NULL DEFAULT 60,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(project_id,ordinal)
  )`,
  `CREATE TABLE IF NOT EXISTS production_versions (
    id uuid PRIMARY KEY,
    episode_id uuid NOT NULL REFERENCES episodes(id) ON DELETE CASCADE,
    job_id uuid UNIQUE REFERENCES generation_jobs(id) ON DELETE SET NULL,
    version integer NOT NULL DEFAULT 1 CHECK (version > 0),
    status text NOT NULL DEFAULT 'queued',
    scene_plan jsonb NOT NULL DEFAULT '{}'::jsonb,
    production_pack jsonb NOT NULL DEFAULT '{}'::jsonb,
    quality_gate_report jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(episode_id,version)
  )`,
  `CREATE TABLE IF NOT EXISTS approvals (
    id uuid PRIMARY KEY,
    production_version_id uuid NOT NULL REFERENCES production_versions(id) ON DELETE CASCADE,
    gate text NOT NULL,
    status text NOT NULL,
    evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
    approved_by text,
    created_at timestamptz NOT NULL DEFAULT now()
  )`,
  `CREATE TABLE IF NOT EXISTS quality_reviews (
    id uuid PRIMARY KEY,
    production_version_id uuid NOT NULL REFERENCES production_versions(id) ON DELETE CASCADE,
    review_type text NOT NULL,
    status text NOT NULL,
    findings jsonb NOT NULL DEFAULT '[]'::jsonb,
    evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
  )`,
  `CREATE TABLE IF NOT EXISTS delivery_receipts (
    id uuid PRIMARY KEY,
    production_version_id uuid NOT NULL REFERENCES production_versions(id) ON DELETE CASCADE,
    output_path text NOT NULL,
    output_sha256 text,
    duration_ms bigint,
    validation_status text NOT NULL,
    manifest jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
  )`,
  `CREATE TABLE IF NOT EXISTS director_capability_reviews (
    id uuid PRIMARY KEY,
    production_version_id uuid NOT NULL REFERENCES production_versions(id) ON DELETE CASCADE,
    capability text NOT NULL CHECK (capability IN ('actor_reaction','limited_mesh','grasp_and_retain','interaction_ready','hyperframes_scene','theory_rule')),
    scope_id text NOT NULL,
    contract_sha256 char(64) NOT NULL CHECK (contract_sha256 ~ '^[0-9a-f]{64}$'),
    status text NOT NULL CHECK (status IN ('APPROVED','REVISION_REQUIRED','REJECTED','REVOKED')),
    reviewer_kind text NOT NULL DEFAULT 'human' CHECK (reviewer_kind='human'),
    reviewer_id text NOT NULL,
    evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
    expires_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
  )`,
  `CREATE TABLE IF NOT EXISTS director_knowledge_candidates (
    id uuid PRIMARY KEY,
    project_id uuid NOT NULL REFERENCES video_projects(id) ON DELETE CASCADE,
    kind text NOT NULL CHECK (kind IN ('theory','observed_grammar','director_experience','project_style','user_preference')),
    status text NOT NULL DEFAULT 'candidate' CHECK (status IN ('candidate','project_approved','rejected')),
    contract_sha256 char(64) NOT NULL CHECK (contract_sha256 ~ '^[0-9a-f]{64}$'),
    content jsonb NOT NULL,
    provenance jsonb NOT NULL,
    approved_by text,
    created_at timestamptz NOT NULL DEFAULT now()
  )`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS project_id uuid REFERENCES video_projects(id)`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS episode_id uuid REFERENCES episodes(id)`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS production_version_id uuid REFERENCES production_versions(id)`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS duration_profile text NOT NULL DEFAULT 'episode_60'`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS aspect_ratio text NOT NULL DEFAULT '16:9' CHECK (aspect_ratio IN ('16:9','9:16'))`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS subtitles_enabled boolean NOT NULL DEFAULT true`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS slide_visual_profile jsonb`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS music_selection jsonb`,
  `CREATE TABLE IF NOT EXISTS music_uploads (
    id uuid PRIMARY KEY,
    user_id text NOT NULL,
    original_name text NOT NULL,
    mime_type text NOT NULL,
    size_bytes integer NOT NULL CHECK (size_bytes > 0 AND size_bytes <= 10485760),
    sha256 char(64) NOT NULL,
    storage_path text NOT NULL,
    deleted_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
  )`,
  `CREATE INDEX IF NOT EXISTS music_uploads_user_idx ON music_uploads(user_id,created_at DESC)`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS scenario_input text`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS remake_of_job_id uuid REFERENCES generation_jobs(id)`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS genre_id text`,
  `ALTER TABLE generation_jobs ADD COLUMN IF NOT EXISTS genre_version text`,
  `CREATE INDEX IF NOT EXISTS episodes_project_idx ON episodes(project_id,ordinal)`,
  `CREATE INDEX IF NOT EXISTS production_versions_episode_idx ON production_versions(episode_id,version DESC)`,
  `CREATE UNIQUE INDEX IF NOT EXISTS approvals_version_gate_idx ON approvals(production_version_id,gate)`,
  `CREATE UNIQUE INDEX IF NOT EXISTS quality_reviews_version_type_idx ON quality_reviews(production_version_id,review_type)`,
  `CREATE UNIQUE INDEX IF NOT EXISTS delivery_receipts_version_idx ON delivery_receipts(production_version_id)`,
  `CREATE INDEX IF NOT EXISTS director_capability_reviews_lookup_idx ON director_capability_reviews(production_version_id,capability,scope_id,created_at DESC)`,
  `CREATE INDEX IF NOT EXISTS director_knowledge_candidates_project_idx ON director_knowledge_candidates(project_id,status,created_at DESC)`,
  `CREATE TABLE IF NOT EXISTS user_notifications (
    id bigserial PRIMARY KEY,
    user_id text NOT NULL,
    job_id uuid NOT NULL REFERENCES generation_jobs(id) ON DELETE CASCADE,
    kind text NOT NULL CHECK (kind IN ('completed')),
    created_at timestamptz NOT NULL DEFAULT now(),
    read_at timestamptz,
    UNIQUE(user_id,job_id,kind)
  )`,
  `CREATE INDEX IF NOT EXISTS user_notifications_unread_idx ON user_notifications(user_id,read_at,created_at DESC)`,
  `CREATE TABLE IF NOT EXISTS time_wallets (
    user_id text PRIMARY KEY,
    balance_seconds bigint NOT NULL DEFAULT 0 CHECK (balance_seconds >= 0),
    reserved_seconds bigint NOT NULL DEFAULT 0 CHECK (reserved_seconds >= 0 AND reserved_seconds <= balance_seconds),
    updated_at timestamptz NOT NULL DEFAULT now()
  )`,
  `CREATE TABLE IF NOT EXISTS time_reservations (
    job_id uuid PRIMARY KEY REFERENCES generation_jobs(id) ON DELETE CASCADE,
    user_id text NOT NULL REFERENCES time_wallets(user_id),
    reserved_seconds bigint NOT NULL CHECK (reserved_seconds > 0),
    charged_seconds bigint NOT NULL DEFAULT 0 CHECK (charged_seconds >= 0),
    status text NOT NULL CHECK (status IN ('reserved','settled','released')),
    created_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz
  )`,
  `CREATE TABLE IF NOT EXISTS time_wallet_entries (
    id bigserial PRIMARY KEY,
    user_id text NOT NULL REFERENCES time_wallets(user_id),
    job_id uuid REFERENCES generation_jobs(id),
    kind text NOT NULL CHECK (kind IN ('grant','settle')),
    seconds bigint NOT NULL,
    external_reference text,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(job_id,kind),
    UNIQUE(external_reference)
  )`,
  `UPDATE generation_jobs job SET continuity_enabled=true,updated_at=now()
    WHERE job.continuity_enabled=false AND job.slide_visual_profile IS NULL AND EXISTS (
      SELECT 1 FROM image_tasks task
      WHERE task.job_id=job.id AND (
        task.task_type='continuity_asset' OR jsonb_array_length(task.reference_asset_ids)>0
      )
    )`,
  `UPDATE generation_jobs SET continuity_enabled=false,updated_at=now()
    WHERE slide_visual_profile IS NOT NULL AND continuity_enabled=true`,
];

type SnapshotRow = {
  relative_path: string;
  sha256: string;
  content: string;
  first_seen: Date;
};

type JobManifestRow = {
  job_id: string;
  manifest: Array<{ relativePath: string; version: number; sha256: string }>;
  first_seen: Date;
};

@Injectable()
export class DatabaseService implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(DatabaseService.name);
  readonly pool = new Pool({ connectionString: config.databaseUrl, max: 8 });

  async onModuleInit() {
    for (const sql of migrations) await this.pool.query(sql);
    await this.backfillPromptHistory();
    this.logger.log("PostgreSQL schema ready");
  }

  async onModuleDestroy() { await this.pool.end(); }

  query<T extends QueryResultRow = QueryResultRow>(text: string, values: unknown[] = []) {
    return this.pool.query<T>(text, values);
  }

  async transaction<T>(fn: (client: PoolClient) => Promise<T>): Promise<T> {
    const client = await this.pool.connect();
    try {
      await client.query("BEGIN");
      const result = await fn(client);
      await client.query("COMMIT");
      return result;
    } catch (error) {
      await client.query("ROLLBACK");
      throw error;
    } finally { client.release(); }
  }

  private async backfillPromptHistory() {
    const snapshots = await this.query<SnapshotRow>(`SELECT relative_path,sha256,(array_agg(content ORDER BY created_at))[1] AS content,min(created_at) AS first_seen
      FROM prompt_snapshots GROUP BY relative_path,sha256 ORDER BY relative_path,first_seen`);
    for (const snapshot of snapshots.rows) {
      await this.transaction(async (client) => {
        await client.query(`SELECT pg_advisory_xact_lock(hashtext($1))`, [snapshot.relative_path]);
        const existing = await client.query(`SELECT version FROM prompt_versions WHERE relative_path=$1 AND sha256=$2`, [snapshot.relative_path, snapshot.sha256]);
        if (!existing.rowCount) {
          await client.query(`INSERT INTO prompt_versions(relative_path,version,sha256,content,created_at)
            SELECT $1,coalesce(max(version),0)+1,$2,$3,$4 FROM prompt_versions WHERE relative_path=$1`,
            [snapshot.relative_path, snapshot.sha256, snapshot.content, snapshot.first_seen]);
        }
      });
    }
    await this.query(`UPDATE prompt_snapshots snapshot SET prompt_version=version.version
      FROM prompt_versions version
      WHERE snapshot.relative_path=version.relative_path AND snapshot.sha256=version.sha256 AND snapshot.prompt_version IS NULL`);

    const jobs = await this.query<JobManifestRow>(`SELECT snapshot.job_id,min(snapshot.created_at) AS first_seen,
      jsonb_agg(jsonb_build_object('relativePath',snapshot.relative_path,'version',snapshot.prompt_version,'sha256',snapshot.sha256) ORDER BY snapshot.relative_path) AS manifest
      FROM prompt_snapshots snapshot
      JOIN generation_jobs job ON job.id=snapshot.job_id
      WHERE job.prompt_set_version IS NULL AND snapshot.prompt_version IS NOT NULL AND snapshot.relative_path=ANY($1::text[])
      GROUP BY snapshot.job_id ORDER BY first_seen`, [ACTIVE_PROMPT_PATHS]);
    for (const job of jobs.rows) {
      const fingerprint = createHash("sha256").update(JSON.stringify(job.manifest), "utf8").digest("hex");
      await this.transaction(async (client) => {
        await client.query(`SELECT pg_advisory_xact_lock(hashtext('slidegen_prompt_sets'))`);
        const set = await client.query<{ version: string }>(`INSERT INTO prompt_sets(fingerprint,manifest) VALUES($1,$2)
          ON CONFLICT(fingerprint) DO UPDATE SET fingerprint=excluded.fingerprint RETURNING version`, [fingerprint, JSON.stringify(job.manifest)]);
        await client.query(`UPDATE generation_jobs SET prompt_set_version=$2 WHERE id=$1 AND prompt_set_version IS NULL`, [job.job_id, set.rows[0].version]);
      });
    }
  }
}
