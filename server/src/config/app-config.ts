import path from "node:path";

const num = (v: string | undefined, fallback: number) => {
  const n = Number(v);
  return Number.isFinite(n) && n > 0 ? n : fallback;
};

const nonNegative = (v: string | undefined, fallback: number) => {
  const n = Number(v);
  return Number.isFinite(n) && n >= 0 ? n : fallback;
};

const bool = (value: string | undefined, fallback = false) => value === undefined
  ? fallback
  : ["1", "true", "yes", "on"].includes(value.toLowerCase());

const codexModel = process.env.CODEX_MODEL ?? "gpt-5.6-luna";

export const config = {
  port: num(process.env.PORT, 3000),
  redisUrl: process.env.REDIS_URL ?? "redis://localhost:6379",
  databaseUrl: process.env.DATABASE_URL ?? "postgresql://slidegen:slidegen@localhost:5432/slidegen",
  runnerUrl: (process.env.RUNNER_URL ?? "http://localhost:8081").replace(/\/$/, ""),
  dataDir: path.resolve(process.env.DATA_DIR ?? "./data"),
  promptsDir: path.resolve(process.env.PROMPTS_DIR ?? path.join(__dirname, "../../../harnesses/classic-slide/prompts")),
  requestsPerMinute: num(process.env.REQUESTS_PER_MINUTE, 120),
  // Zero disables the daily quota while pending-job limits still protect capacity.
  dailyJobs: nonNegative(process.env.DAILY_JOBS, 0),
  userPending: num(process.env.USER_PENDING, 20),
  globalPending: num(process.env.GLOBAL_PENDING, 20),
  corsOrigins: (process.env.CORS_ORIGIN ?? "").split(",").map((o) => o.trim()).filter(Boolean),
  jobTimeoutMs: num(process.env.JOB_TIMEOUT_MINUTES, 60) * 60_000,
  videoJobGlobalConcurrency: Math.min(1, Math.floor(num(process.env.VIDEO_JOB_GLOBAL_CONCURRENCY, 1))),
  concurrency: Math.min(1, Math.floor(num(process.env.WORKER_CONCURRENCY, 1))),
  retentionMs: num(process.env.JOB_RETENTION_HOURS, 72) * 3_600_000,
  maxScenarioChars: 20_000,
  usdKrwRate: num(process.env.USD_KRW_RATE, 1388.1),
  codexModel,
  codexReasoningEffort: (process.env.CODEX_REASONING_EFFORT ?? "max").toLowerCase(),
  codexFastMode: bool(process.env.CODEX_FAST_MODE),
  videoFps: Math.floor(num(process.env.VIDEO_FPS, 24)),
  imageConcurrency: Math.min(16, Math.floor(num(process.env.IMAGE_TASK_CONCURRENCY, 12))),
  voiceConcurrency: Math.floor(num(process.env.VOICE_TASK_CONCURRENCY, 2)),
  voiceProvider: (process.env.VOICE_PROVIDER ?? "mock").toLowerCase(),
  microsoftEdgeVoice: process.env.MICROSOFT_EDGE_VOICE ?? "ko-KR-InJoonNeural",
  microsoftEdgeRate: process.env.MICROSOFT_EDGE_RATE ?? "-30%",
  microsoftEdgePitch: process.env.MICROSOFT_EDGE_PITCH ?? "+0Hz",
  microsoftEdgeVolume: process.env.MICROSOFT_EDGE_VOLUME ?? "+0%",
  elevenLabsConfigured: bool(process.env.ELEVENLABS_CONFIGURED),
  elevenLabsVoiceId: process.env.ELEVENLABS_VOICE_ID ?? "nPczCjzI2devNBz1zQrb",
  elevenLabsVoiceName: process.env.ELEVENLABS_VOICE_NAME ?? "Brian - Deep, Resonant and Comforting",
  elevenLabsModel: process.env.ELEVENLABS_MODEL_ID ?? "eleven_flash_v2_5",
  elevenLabsStability: Number(process.env.ELEVENLABS_STABILITY ?? 0.6),
  elevenLabsSimilarityBoost: Number(process.env.ELEVENLABS_SIMILARITY_BOOST ?? 0.6),
  elevenLabsSpeed: Number(process.env.ELEVENLABS_SPEED ?? 0.7),
  codexModelOptions: Array.from(new Set(
    (process.env.CODEX_MODEL_OPTIONS ?? `gpt-5.6-luna,gpt-5.6-terra,gpt-5.6-sol,${codexModel}`)
      .split(",").map((value) => value.trim()).filter(Boolean),
  )),
};

export const redisConnection = () => {
  const url = new URL(config.redisUrl);
  return {
    host: url.hostname,
    port: Number(url.port || 6379),
    password: process.env.REDIS_PASSWORD_FILE ? require('node:fs').readFileSync(process.env.REDIS_PASSWORD_FILE, 'utf8').trim() : url.password || undefined,
    maxRetriesPerRequest: null,
  };
};
