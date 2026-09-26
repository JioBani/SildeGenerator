import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import "./app.css";
import { PromptManager } from "./PromptManager";
import { AnalyticsDashboard } from "./AnalyticsDashboard";
import { CodexTranscriptPanel } from "./CodexTranscriptPanel";
import { ModelSettings } from "./ModelSettings";
import { VoiceSettings } from "./VoiceSettings";
import { HarnessSettings } from "./HarnessSettings";
import { ActiveStageTable, StageTimeline } from "./StageTimeline";
import { CostDiagram } from "./CostDiagram";
import { estimateNarrationDuration, formatPlaybackDuration } from "./duration-estimate";
import { VideoPreview } from "./VideoPreview";

type JobStatus = {
  id: string;
  userId?: string;
  status: "queued" | "waiting" | "running" | "completed" | "failed" | string;
  currentStage?: string;
  progress: number;
  error: string | null;
  queuedAt?: string;
  startedAt?: string;
  finishedAt?: string;
  totalDurationMs?: number | string | null;
  promptSetVersion?: number | string | null;
  qualityScore?: number | string | null;
  imageModel?: string | null;
  imageStyle?: string | null;
  motionStyle?: { id: "narrative" | "educational_info"; version: string; productionRoute?: "local_graphic" } | null;
  slideVisualProfile?: { id: "local_illustration"; version: string; imageStyle: ImageStyle } | null;
  musicSelection?: { mode: "none" | "auto" | "upload"; preset?: string } | null;
  genreId?: string | null;
  genreVersion?: string | null;
  continuityEnabled?: boolean;
  videoFps?: number;
  voiceConcurrency?: number;
  voiceProvider?: string | null;
  voiceModel?: string | null;
  voiceId?: string | null;
  narrationSpeed?: number;
  harnessId?: string | null;
  harnessVersion?: string | null;
  episodeNumber?: number | null;
  episodeTitle?: string | null;
  durationProfile?: string | null;
  aspectRatio?: "16:9" | "9:16";
  subtitlesEnabled?: boolean;
  qualityGateStatus?: string | null;
  reviewStatus?: string | null;
  queuePosition?: number | null;
  jobsAhead?: number | null;
  activeJobs?: number | null;
  queuedJobs?: number | null;
  queueWaitMs?: number | string | null;
  generationTimePerVideoMinuteMs?: number | string | null;
  costPerVideoMinuteKrw?: number | string | null;
};

type MyJob = {
  id: string;
  title: string;
  status: string;
  currentStage: string | null;
  progress: number;
  error: string | null;
  queuedAt: string;
  finishedAt: string | null;
  durationProfile: string;
  videoDurationMs: number | null;
  hasThumbnail: boolean;
};
type JobNotification = { id: string; jobId: string; title: string; kind: string; createdAt: string };
type ScriptEstimate = { title: string | null; narrationText: string; narrationChars: number; estimatedSeconds: number; maximumSeconds: number };
type TimeWallet = { enabled: boolean; balanceSeconds?: number; reservedSeconds?: number; availableSeconds?: number };

type ImageModel = "gpt-image-2" | "gpt-image-2.5-sunburst" | "gpt-image-2.5-flare";
type ImageStyle = "editorial_illustration" | "cinematic_realism" | "graphic_explainer" | "cute_character" | "fantasy_anime" | "animation_3d" | "disney_animation" | "dystopian";
type MotionStyleId = "narrative" | "educational_info";
type HarnessOption = { id: string; version: string; display_name: string; description: string; compatible: boolean; public: boolean };

const IMAGE_MODEL_OPTIONS: Array<{ value: ImageModel; label: string; note: string }> = [
  { value: "gpt-image-2", label: "GPT Image 2", note: "낮은 API 단가" },
  { value: "gpt-image-2.5-sunburst", label: "GPT Image 2.5 Sunburst", note: "최고 품질 · 기본값" },
  { value: "gpt-image-2.5-flare", label: "GPT Image 2.5 Flare", note: "빠른 2.5" },
];
const IMAGE_STYLE_OPTIONS: Array<{ value: ImageStyle; label: string; note: string; preview: string }> = [
  { value: "cute_character", label: "귀여운 캐릭터", note: "따뜻한 그림책 분위기", preview: "slide-character-original" },
  { value: "fantasy_anime", label: "판타지 애니메이션", note: "손그림 배경과 셀 채색", preview: "slide-fantasy-original" },
  { value: "cinematic_realism", label: "실사 영화", note: "사실적인 인물과 영화적 조명", preview: "cinematic-realism-v1" },
  { value: "animation_3d", label: "3D 애니메이션", note: "입체적인 인물과 촉감 있는 재질", preview: "animation-3d-v1" },
  { value: "disney_animation", label: "디즈니풍", note: "풍부한 표정과 손그림 애니메이션", preview: "disney-animation-v1" },
  { value: "dystopian", label: "디스토피아", note: "압도적인 공간과 긴장감 있는 분위기", preview: "dystopian-v1" },
];
const CINEMATIC_STYLE_IDS: ImageStyle[] = ["cinematic_realism", "animation_3d", "disney_animation", "dystopian"];
const MOTION_STYLE_OPTIONS: Array<{ value: MotionStyleId; label: string; note: string; preview: string }> = [
  { value: "narrative", label: "내러티브형", note: "주체의 변화가 더 큰 맥락과 결과로 이어집니다", preview: "/style-previews/motion-narrative.svg" },
  { value: "educational_info", label: "교육·정보형", note: "질문과 원리를 도식·단계·비교로 풉니다", preview: "/style-previews/motion-educational.svg" },
];

type Dashboard = {
  jobs: { total: number; completed: number; failed: number; active: number; averageDurationMs: number | string };
  usage: {
    inputTokens: number | string;
    cachedInputTokens: number | string;
    outputTokens: number | string;
    reasoningTokens: number | string;
    characters: number | string;
    images: number | string;
    actualCostKrw: number | string;
    apiEquivalentCostKrw: number | string;
    codexApiEquivalentCostKrw: number | string;
    imageApiEquivalentCostKrw: number | string;
  };
  stages: Array<{ stage: string; runs: number; averageDurationMs: number | string; totalDurationMs: number | string }>;
  queue: {
    activeJobs: number | null;
    queuedJobs: number | null;
    oldestWaitMs: number | string | null;
    globalConcurrency: number;
    queueWaitP50Ms: number | string | null;
    queueWaitP95Ms: number | string | null;
  };
};

type JobDetail = {
  job: Record<string, unknown> | null;
  promptSet: null | { version: number | string; fingerprint: string; manifest: Array<{ relativePath: string; version: number; sha256: string }> };
  metrics: null | {
    jobId: string;
    totalGenerationTimeMs: number;
    videoDurationMs: number;
    promptSetVersion: number | null;
    model: string;
    effort: string;
    imageModel: string;
    voiceModel: string;
    qualityScore: number | null;
    qualityNote: string | null;
    codexInputTokens: number;
    codexOutputTokens: number;
    codexReasoningTokens: number;
    imageInputTokens: number;
    imageOutputTokens: number;
    imageTokens: number;
    imageCount: number;
    voiceCharacters: number;
    voiceDurationMs: number;
    inferenceCostKrw: number;
    imageCostKrw: number;
    imageApiEstimatedCostKrw: number;
    imageApiEstimatedCostUsd: number;
    imageApiExchangeRateUsdKrw: number;
    voiceCostKrw: number;
    actualExternalCostKrw: number;
    unpricedEvents: number;
    costComplete: boolean;
    totalCostKrw: number;
    inferenceCostPerVideoMinuteKrw: number | null;
    imageCostPerImageKrw: number | null;
    voiceCostPerMinuteKrw: number | null;
    totalCostPerVideoMinuteKrw: number | null;
    stages: Array<{ stage: string; runs: number; wallClockDurationMs: number | string; totalDurationMs: number | string; averageDurationMs: number | string }>;
  };
  stages: Array<Record<string, unknown>>;
  usage: Array<Record<string, unknown>>;
  assets: Array<Record<string, unknown>>;
  prompts: Array<Record<string, unknown>>;
  events: Array<Record<string, unknown>>;
  imageTasks: Array<Record<string, unknown>>;
  imageAttempts: Array<Record<string, unknown>>;
  voiceTasks: Array<Record<string, unknown>>;
  voiceAttempts: Array<Record<string, unknown>>;
  renderSegments: Array<Record<string, unknown>>;
};

const TOKEN_KEY = "slidegen.token";
const RECENT_JOB_KEY = "slidegen.recentJobId";
const API_BASE = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "";

const STATUS_LABELS: Record<string, string> = {
  queued: "대기 중",
  waiting: "대기 중",
  running: "생성 중",
  completed: "완료",
  failed: "실패",
};

const STAGE_LABELS: Record<string, string> = {
  queue_wait: "대기열",
  retry_wait: "재시도 대기",
  job_initialization: "작업 준비",
  harness_loading: "영상 연출 불러오기",
  prompt_loading: "프롬프트 불러오기",
  scene_planning: "장면 구성",
  image_generation: "이미지 생성",
  keycut_generation: "기준 키컷 생성",
  voice_generation: "음성 생성",
  subtitle_generation: "자막 생성",
  audio_assembly: "음성 조립",
  video_render: "영상 렌더링",
  asset_generation: "이미지·음성 생성",
  progressive_video_render: "선행 구간 렌더링",
  segment_render: "장면 구간 렌더링",
  video_assembly: "영상 조립",
  deterministic_validation: "결과 검사",
  done: "완료",
  failed: "실패",
};

const statusLabel = (value?: string) => value ? STATUS_LABELS[value] ?? value : "-";
const stageLabel = (value?: string) => value ? STAGE_LABELS[value] ?? value : "-";

const won = (value: unknown) => `${(Number(value) || 0).toLocaleString("ko-KR", { maximumFractionDigits: 2, minimumFractionDigits: 0 })}원`;
const duration = (value: unknown) => {
  const seconds = Math.round((Number(value) || 0) / 1000);
  const minutes = Math.floor(seconds / 60);
  return minutes ? `${minutes}분 ${seconds % 60}초` : `${seconds}초`;
};
const integer = (value: unknown) => (Number(value) || 0).toLocaleString("ko-KR");

export function App() {
  const [detailJobId] = useState(() => new URLSearchParams(window.location.search).get("adminJob"));
  const [requestedJobId] = useState(() => new URLSearchParams(window.location.search).get("job"));
  const [tab, setTab] = useState<"create" | "admin">(() => detailJobId ? "admin" : "create");
  const [adminView, setAdminView] = useState<"overview" | "analytics" | "prompts" | "settings">("overview");
  const [overviewSection, setOverviewSection] = useState<"jobs" | "metrics">("jobs");
  const [detailSection, setDetailSection] = useState<"summary" | "pipeline" | "cost">("summary");
  const [settingsSection, setSettingsSection] = useState<"codex" | "voice" | "harness">("codex");
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) ?? "");
  const [scenario, setScenario] = useState("");
  const [imageModel, setImageModel] = useState<ImageModel>("gpt-image-2.5-sunburst");
  const [imageStyle, setImageStyle] = useState<ImageStyle>("cute_character");
  const [motionStyleId, setMotionStyleId] = useState<MotionStyleId>("narrative");
  const [localSlideImages, setLocalSlideImages] = useState(false);
  const [musicMode, setMusicMode] = useState<"none" | "auto" | "upload">("none");
  const [musicUpload, setMusicUpload] = useState<{ id: string; name: string } | null>(null);
  const [musicUploadProgress, setMusicUploadProgress] = useState<number | null>(null);
  const [musicPreviewUrl, setMusicPreviewUrl] = useState<string | null>(null);
  const [continuityEnabled, setContinuityEnabled] = useState(false);
  const [harnessId, setHarnessId] = useState("astra-motion");
  const [narrationSpeed, setNarrationSpeed] = useState(0.7);
  const [aspectRatio, setAspectRatio] = useState<"16:9" | "9:16">("16:9");
  const [subtitlesEnabled, setSubtitlesEnabled] = useState(true);
  const [harnesses, setHarnesses] = useState<HarnessOption[]>([]);
  const [optionsReady, setOptionsReady] = useState(false);
  const [optionsError, setOptionsError] = useState("");
  const [optionsAttempt, setOptionsAttempt] = useState(0);
  const [connectionError, setConnectionError] = useState("");
  const [estimateError, setEstimateError] = useState("");
  const videoKindLabel = harnessId === "astra-motion" ? "모션그래픽 영상"
    : harnessId === "hybrid-story" ? "모션·슬라이드 혼합 영상" : "슬라이드 영상";
  const [productionMode, setProductionMode] = useState<{ imageProvider: string; motionImageProvider?: string; motionProductionAvailable?: boolean; voiceProvider: string; slideV05LocalImages?: boolean; supportedImageModels?: ImageModel[]; imageGenerationPausedUntilUnix?: number } | null>(null);
  const [job, setJob] = useState<JobStatus | null>(null);
  const selectedJobRequest = useRef(0);
  const currentToken = useRef(token);
  currentToken.current = token;
  const [remaking, setRemaking] = useState(false);
  const listBackoffUntil = useRef(0);
  const [myJobs, setMyJobs] = useState<MyJob[]>([]);
  const [notifications, setNotifications] = useState<JobNotification[]>([]);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [jobs, setJobs] = useState<JobStatus[]>([]);
  const [detail, setDetail] = useState<JobDetail | null>(null);
  const [adminLoading, setAdminLoading] = useState(false);
  const [restorePending, setRestorePending] = useState(true);
  const [scriptEstimate, setScriptEstimate] = useState<ScriptEstimate | null>(null);
  const [timeWallet, setTimeWallet] = useState<TimeWallet | null>(null);
  const forcedLocalSlides = productionMode?.slideV05LocalImages === true && productionMode.imageProvider === "mock";
  const localGraphics = (harnessId === "astra-motion" ? productionMode?.motionImageProvider ?? productionMode?.imageProvider : productionMode?.imageProvider) === "local_graphic";
  const supportsLocalIllustrations = imageStyle === "cute_character" || imageStyle === "fantasy_anime";
  const localIllustrations = harnessId === "classic-slide" && productionMode?.slideV05LocalImages === true && localSlideImages && supportsLocalIllustrations;
  const imageGenerationPaused = productionMode?.imageProvider === "oauth"
    && !localIllustrations && !localGraphics
    && (productionMode.imageGenerationPausedUntilUnix ?? 0) * 1000 > Date.now();
  useEffect(() => () => { if (musicPreviewUrl) URL.revokeObjectURL(musicPreviewUrl); }, [musicPreviewUrl]);
  const hasNarrationLabels = /(?:나레이션|내레이션)[*_\s]*[:：]/.test(scenario);
  const durationEstimate = useMemo(() => estimateNarrationDuration(scenario, narrationSpeed), [narrationSpeed, scenario]);
  const maximumVideoSeconds = ["classic-slide", "cinematic-slide"].includes(harnessId) ? 1800 : 60;
  const estimatedSeconds = scriptEstimate?.estimatedSeconds ?? (hasNarrationLabels ? null : durationEstimate?.centerSeconds ?? null);
  const overDurationLimit = estimatedSeconds !== null && estimatedSeconds > maximumVideoSeconds;
  const estimatedUsageSeconds = estimatedSeconds === null ? null : Math.max(1, Math.ceil(estimatedSeconds));
  const insufficientTime = timeWallet?.enabled === true && estimatedUsageSeconds !== null && estimatedUsageSeconds > (timeWallet.availableSeconds ?? 0);

  useEffect(() => {
    setEstimateError("");
    if (!scenario.trim()) { setScriptEstimate(null); return; }
    setScriptEstimate(null);
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      void fetch(API_BASE + "/api/jobs/estimate", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario, narrationSpeed, harnessId }), signal: controller.signal,
      }).then(async (response) => {
        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          throw new Error(String(payload.message ?? "대본을 분석하지 못했습니다. 잠시 후 다시 시도해 주세요."));
        }
        const result: unknown = await response.json();
        if (!result || typeof result !== "object" ||
            !Number.isFinite((result as ScriptEstimate).estimatedSeconds) ||
            !Number.isFinite((result as ScriptEstimate).narrationChars)) throw new Error("invalid estimate");
        if (!controller.signal.aborted) setScriptEstimate(result as ScriptEstimate);
      }).catch((reason) => { if (!controller.signal.aborted) { setScriptEstimate(null); setEstimateError(reason instanceof Error ? reason.message : "대본 분석 연결이 끊어졌습니다."); } });
    }, 300);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [scenario, narrationSpeed, harnessId]);

  useEffect(() => localStorage.setItem(TOKEN_KEY, token), [token]);

  useEffect(() => {
    const controller = new AbortController();
    setOptionsReady(false);
    setOptionsError("");
    void Promise.all(["harnesses", "production"].map(async name => {
      const response = await fetch(API_BASE + `/api/jobs/options/${name}`, { signal: controller.signal });
      if (!response.ok) throw new Error("제작 설정을 불러오지 못했습니다. 연결을 확인하고 다시 시도해 주세요.");
      return response.json();
    })).then(([items, production]) => {
      if (controller.signal.aborted) return;
      if (!Array.isArray(items) || !production?.imageProvider || !production?.voiceProvider) throw new Error("제작 설정이 올바르지 않습니다. 다시 불러와 주세요.");
      const available = items.filter((item: HarnessOption) => item.compatible && item.public && ["astra-motion", "classic-slide", "cinematic-slide", "narrative-slide", "hybrid-story"].includes(item.id))
        .filter((item: HarnessOption) => production.slideV05LocalImages && production.imageProvider === "mock" ? item.id === "classic-slide" : production.imageProvider !== "local_graphic" || item.id === "astra-motion");
      if (!available.length) throw new Error("현재 사용 가능한 영상 구성 방식이 없습니다.");
      setHarnesses(available);
      setProductionMode(production);
      setHarnessId(current => available.some((item: HarnessOption) => item.id === current) ? current : available[0].id);
      setOptionsReady(true);
    }).catch(reason => { if (!controller.signal.aborted) setOptionsError(reason.message ?? "제작 서비스에 연결할 수 없습니다."); });
    return () => controller.abort();
  }, [optionsAttempt]);
  useEffect(() => {
    if (productionMode?.supportedImageModels?.length && !productionMode.supportedImageModels.includes(imageModel)) {
      setImageModel(productionMode.supportedImageModels[0]);
    }
  }, [productionMode, imageModel]);

  const api = useCallback((url: string, init?: RequestInit, authenticated = true) => {
    const headers = new Headers(init?.headers);
    if (authenticated && token.trim()) headers.set("Authorization", `Bearer ${token.trim()}`);
    return fetch(API_BASE + url, { ...init, headers });
  }, [token]);

  const refreshMyJobs = useCallback(async () => {
    if (!token) { setMyJobs([]); setNotifications([]); setTimeWallet(null); return; }
    if (Date.now() < listBackoffUntil.current) return;
    const [jobResponse, notificationResponse, walletResponse] = await Promise.all([
      api('/api/jobs'), api('/api/jobs/notifications'), api('/api/jobs/wallet'),
    ]);
    if (currentToken.current !== token) return;
    if ([jobResponse, notificationResponse, walletResponse].some(response => response.status === 429)) {
      listBackoffUntil.current = Date.now() + 60_000;
      setConnectionError("조회 요청이 많아 잠시 후 자동으로 다시 확인합니다. 제작 작업은 계속됩니다.");
      return;
    }
    if (jobResponse.status === 401 || jobResponse.status === 403) {
      setMyJobs([]); setNotifications([]); setTimeWallet(null);
      setConnectionError("접근 토큰이 거부되었습니다. 올바른 토큰인지 확인해 주세요.");
      return;
    }
    if (jobResponse.ok) setConnectionError("");
    if (jobResponse.ok) setMyJobs(await jobResponse.json());
    if (notificationResponse.ok) setNotifications(await notificationResponse.json());
    if (walletResponse.ok) setTimeWallet(await walletResponse.json());
  }, [api, token]);

  useEffect(() => {
    const refreshVisible = () => { if (document.visibilityState === "visible") void refreshMyJobs().catch(() => undefined); };
    refreshVisible();
    if (!token) return;
    const timer = window.setInterval(refreshVisible, 30_000);
    document.addEventListener("visibilitychange", refreshVisible);
    return () => { window.clearInterval(timer); document.removeEventListener("visibilitychange", refreshVisible); };
  }, [refreshMyJobs, token]);

  async function selectMyJob(id: string) {
    const request = ++selectedJobRequest.current;
    setError("");
    try {
      const response = await api(`/api/jobs/${id}`);
      if (!response.ok) throw new Error('작업을 불러오지 못했습니다. 접근 토큰과 연결을 확인해 주세요.');
      const selected = await response.json();
      if (request !== selectedJobRequest.current || currentToken.current !== token) return;
      localStorage.setItem(RECENT_JOB_KEY, id);
      setJob(selected);
    } catch { if (request === selectedJobRequest.current) setError('작업을 불러오지 못했습니다. 다시 선택해 주세요.'); }
  }

  async function openNotification(notification: JobNotification) {
    await selectMyJob(notification.jobId);
    await api(`/api/jobs/notifications/${notification.id}/read`, { method: 'POST' });
    setNotifications((items) => items.filter((item) => item.id !== notification.id));
  }

  useEffect(() => {
    if (!restorePending || !token || job) return;
    let active = true;
    const id = requestedJobId ?? localStorage.getItem(RECENT_JOB_KEY);
    if (!id) { setRestorePending(false); return; }
    void api(`/api/jobs/${id}`).then(async (response) => {
      const result = response.ok ? await response.json() : null;
      if (!active) return;
      if (result) setJob(result);
      else if ([404, 410].includes(response.status)) localStorage.removeItem(RECENT_JOB_KEY);
    }).catch(() => { if (active) setError("이전 작업을 불러오지 못했습니다. 작업 목록에서 다시 선택해 주세요."); }).finally(() => { if (active) setRestorePending(false); });
    return () => { active = false; };
  }, [api, job, requestedJobId, restorePending, token]);

  useEffect(() => {
    if (!job || ["completed", "failed"].includes(job.status)) return;
    let cancelled = false;
    let timer: number;
    const poll = async () => {
      let nextPoll = 5_000;
      try {
        if (document.visibilityState !== "visible") return;
        const response = await api(`/api/jobs/${job.id}`);
        if (response.status === 429) nextPoll = 60_000;
        if (response.ok) {
          const updated = await response.json();
          if (!cancelled) { setJob(updated); setConnectionError(""); }
        }
        else if (!cancelled) setConnectionError(response.status === 401 || response.status === 403 ? "접근 토큰을 확인해 주세요. 제작 상태를 조회할 수 없습니다." : "제작 상태 연결이 끊어졌습니다. 자동으로 다시 확인합니다.");
      } catch {
        if (!cancelled) setConnectionError("제작 상태 연결이 끊어졌습니다. 자동으로 다시 확인합니다.");
      } finally {
        if (!cancelled) timer = window.setTimeout(poll, nextPoll);
      }
    };
    timer = window.setTimeout(poll, 2_000);
    return () => { cancelled = true; window.clearTimeout(timer); };
  }, [api, job?.id, job?.status]);

  useEffect(() => {
    if (!job || !job.slideVisualProfile || !productionMode?.slideV05LocalImages ||
        ["completed", "failed"].includes(job.status)) return;
    const controller = new AbortController();
    const id = job.id;
    void (async () => {
      const response = await api(`/api/jobs/${id}/events`, {
        headers: { Accept: "text/event-stream" }, signal: controller.signal,
      });
      if (!response.ok || !response.body) return;
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let pending = "";
      while (!controller.signal.aborted) {
        const { value, done } = await reader.read();
        if (done) break;
        pending += decoder.decode(value, { stream: true });
        const events = pending.split("\n\n");
        pending = events.pop() ?? "";
        for (const event of events) {
          const data = event.split("\n").filter((line) => line.startsWith("data:")).map((line) => line.slice(5).trim()).join("\n");
          if (!data) continue;
          const updated = JSON.parse(data) as JobStatus;
          if (updated.id === id && !controller.signal.aborted) setJob(updated);
        }
      }
    })().catch(() => { /* Existing polling recovers from SSE failures. */ });
    return () => controller.abort();
  }, [api, job?.id, job?.status, job?.slideVisualProfile?.version, productionMode?.slideV05LocalImages]);

  const refreshAdmin = useCallback(async () => {
    setAdminLoading(true);
    setError("");
    try {
      const [summaryResponse, jobsResponse] = await Promise.all([
        api("/api/admin/dashboard", undefined, false),
        api("/api/admin/jobs?limit=100", undefined, false),
      ]);
      if (!summaryResponse.ok || !jobsResponse.ok) throw new Error("관리자 데이터를 불러오지 못했습니다.");
      setDashboard(await summaryResponse.json());
      setJobs(await jobsResponse.json());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setAdminLoading(false);
    }
  }, [api]);

  useEffect(() => {
    if (tab === "admin" && adminView === "overview" && !detailJobId) void refreshAdmin();
  }, [adminView, detailJobId, refreshAdmin, tab]);

  useEffect(() => {
    if (!detailJobId) return;
    setError("");
    void api(`/api/admin/jobs/${detailJobId}`, undefined, false).then(async (response) => {
      if (!response.ok) throw new Error("작업 상세를 불러오지 못했습니다.");
      setDetail(await response.json());
    }).catch((reason) => setError(reason instanceof Error ? reason.message : String(reason)));
  }, [api, detailJobId]);

  async function submit() {
    setError("");
    const invalid = !scenario.trim() ? ["대본을 입력해 주세요.", "scenario"]
      : !token.trim() ? ["접근 토큰을 입력해 주세요.", "token"]
      : !optionsReady ? [optionsError || "제작 설정을 불러오는 중입니다. 잠시 후 다시 눌러 주세요.", "creative-harness"]
      : !harnesses.some(item => item.id === harnessId) ? ["사용 가능한 영상 구성 방식을 선택해 주세요.", "creative-harness"]
      : estimateError ? [estimateError, "scenario"]
      : !scriptEstimate ? ["읽을 문장을 분석하는 중입니다. 잠시 후 다시 눌러 주세요.", "scenario"]
      : overDurationLimit ? [`예상 길이가 ${formatPlaybackDuration(maximumVideoSeconds)}를 넘습니다. 대본을 줄이거나 나레이션 속도를 높여 주세요.`, "narration-speed"]
      : insufficientTime ? ["제작 가능 시간이 부족합니다. 이용 가능 시간을 확인해 주세요.", "narration-speed"]
      : imageGenerationPaused ? [`구독 이미지 생성 한도에 도달했습니다. ${new Date((productionMode?.imageGenerationPausedUntilUnix ?? 0) * 1000).toLocaleString("ko-KR", { timeZone: "Asia/Seoul" })} 이후 다시 시도해 주세요.`, "creative-harness"]
      : harnessId === "astra-motion" && productionMode?.motionProductionAvailable === false ? ["이 시험 환경에서는 모션 장면 설계가 비활성화되어 있습니다. 실제 모션 제작에는 감독 설계 연결이 필요합니다.", "creative-harness"]
      : forcedLocalSlides && harnessId === "classic-slide" && !localIllustrations ? ["이 시험 사이트에는 AI 장면 이미지가 연결되지 않았습니다. 로컬 도형 삽화 시험 옵션을 선택해야 제작할 수 있습니다.", "local-slide-images"]
      : harnessId === "classic-slide" && musicMode === "upload" && !musicUpload ? ["배경음악 파일을 먼저 올려 주세요.", "music-file"] : null;
    if (invalid) {
      setFormError(invalid[0]);
      document.getElementById(invalid[1])?.focus();
      return;
    }
    setFormError("");
    setSubmitting(true);
    try {
      const response = await api("/api/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario, ...(localGraphics || localIllustrations ? {} : { imageModel }), ...(harnessId === "astra-motion" ? { motionStyleId } : { imageStyle }), ...(localIllustrations ? { sceneVisualMode: "local_illustration" } : {}), ...(harnessId === "classic-slide" && productionMode?.slideV05LocalImages ? { musicMode, ...(musicMode === "upload" ? { musicUploadId: musicUpload?.id } : {}) } : {}), continuityEnabled: localGraphics || localIllustrations ? false : continuityEnabled, harnessId, narrationSpeed, aspectRatio, subtitlesEnabled }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        setFormError(response.status === 401 ? "접근 토큰이 거부되었습니다. 올바른 토큰인지 확인해 주세요." : String(payload.message ?? payload.error ?? response.statusText));
        if (response.status === 401) document.getElementById("token")?.focus();
        return;
      }
      localStorage.setItem(RECENT_JOB_KEY, payload.id);
      setJob({ ...payload, queuePosition: null, jobsAhead: null });
      void refreshMyJobs();
    } catch {
      setFormError("제작 서비스에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.");
    } finally {
      setSubmitting(false);
    }
  }

  async function uploadMusic(file: File) {
    setFormError("");
    setMusicUploadProgress(0);
    if (!token.trim()) {
      setFormError("배경음악을 올리려면 접근 토큰을 먼저 입력해 주세요.");
      document.getElementById("token")?.focus();
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setFormError("배경음악 파일은 10MB 이하만 올릴 수 있습니다.");
      return;
    }
    const form = new FormData();
    form.append("file", file);
    const request = new XMLHttpRequest();
    request.open("POST", API_BASE + "/api/jobs/music");
    request.setRequestHeader("Authorization", `Bearer ${token}`);
    request.upload.onprogress = (event) => {
      if (event.lengthComputable) setMusicUploadProgress(Math.round(event.loaded / event.total * 100));
    };
    request.onload = () => {
      setMusicUploadProgress(null);
      let payload: { id?: string; name?: string; message?: string } = {};
      try { payload = JSON.parse(request.responseText || "{}"); } catch { /* Proxy errors may be HTML. */ }
      if (request.status >= 200 && request.status < 300 && payload.id && payload.name) {
        setMusicUpload({ id: payload.id, name: payload.name });
        setMusicMode("upload");
      } else setFormError(payload.message || "배경음악 업로드에 실패했습니다.");
    };
    request.onerror = () => { setMusicUploadProgress(null); setFormError("배경음악 업로드 중 연결이 끊어졌습니다."); };
    request.send(form);
  }

  async function previewMusic() {
    if (!musicUpload) return;
    const response = await api(`/api/jobs/music/${musicUpload.id}`);
    if (!response.ok) { setFormError("배경음악을 불러오지 못했습니다."); return; }
    setMusicPreviewUrl(URL.createObjectURL(await response.blob()));
  }

  async function removeMusic() {
    if (!musicUpload) return;
    const response = await api(`/api/jobs/music/${musicUpload.id}`, { method: "DELETE" });
    if (!response.ok) { setFormError("배경음악을 삭제하지 못했습니다."); return; }
    setMusicUpload(null);
    setMusicMode("none");
    setMusicPreviewUrl(null);
  }

  async function remake() {
    if (!job || remaking) return;
    setError("");
    setRemaking(true);
    try {
    const response = await api(`/api/jobs/${job.id}/remake`, { method: "POST" });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) { setError(payload.message ?? "다시 만들기를 시작하지 못했습니다."); return; }
    localStorage.setItem(RECENT_JOB_KEY, payload.id);
    setJob({ ...payload, queuePosition: null, jobsAhead: null });
    void refreshMyJobs();
    } catch { setError("다시 만들기 서비스에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요."); }
    finally { setRemaking(false); }
  }

  async function downloadJob(id: string) {
    try {
    const response = await api(`/api/jobs/${id}/video`);
    if (!response.ok) return setError("완성 영상을 내려받지 못했습니다. 이 작업을 만든 접근 토큰인지 확인해 주세요.");
    await saveVideo(response, id);
    } catch { setError("영상 다운로드 연결이 끊어졌습니다. 다시 시도해 주세요."); }
  }

  async function downloadAdminJob(id: string) {
    const response = await api(`/api/admin/jobs/${id}/video`, undefined, false);
    if (!response.ok) return setError("관리자 영상 파일을 내려받지 못했습니다. 파일 보존 기간이 지났는지 확인해 주세요.");
    await saveVideo(response, id);
  }

  async function saveVideo(response: Response, id: string) {
    const url = URL.createObjectURL(await response.blob());
    const anchor = Object.assign(document.createElement("a"), { href: url, download: `slide-${id}.mp4` });
    anchor.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 30_000);
  }

  async function download() {
    if (job) await downloadJob(job.id);
  }

  async function review(verdict: "APPROVED" | "REVISION_REQUIRED") {
    if (!job) return;
    setError("");
    const response = await api(`/api/jobs/${job.id}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ verdict }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) return setError(payload.message ?? "검수 결과를 저장하지 못했습니다.");
    setJob({ ...job, reviewStatus: payload.reviewStatus });
  }

  function openDetailInNewTab(id: string) {
    const url = new URL(window.location.href);
    url.search = "";
    url.hash = "";
    url.searchParams.set("adminJob", id);
    window.open(url.toString(), "_blank", "noopener,noreferrer");
  }

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand"><span className="brand-mark">S</span><span>Slide Generator</span></div>
        <nav aria-label="주 메뉴">
          <button className={tab === "create" ? "active" : ""} onClick={() => setTab("create")}>영상 생성</button>
          <button className={tab === "admin" ? "active" : ""} onClick={() => setTab("admin")}>관리자</button>
        </nav>
      </header>

      {tab === "create" ? (
        <main className="page create-page">
          {notifications.length > 0 && <div className="completion-notice" role="status">
            <strong>영상이 완성됐습니다</strong>
            {notifications.map((item) => <button key={item.id} type="button" onClick={() => void openNotification(item)}>{item.title} 확인</button>)}
          </div>}
          <section className="hero">
            <p className="eyebrow">NARRATED VIDEO</p>
            <h1>대본 하나로 완성하는<br />{videoKindLabel}</h1>
            <p>장면 구성, 이미지, 한국어 음성, 자막과 전환 효과를 자동으로 만듭니다.</p>
          </section>

          <section className="panel composer">
            <label htmlFor="token">접근 토큰</label>
            <input id="token" type="password" autoComplete="off" placeholder="관리자가 발급한 토큰" value={token} onChange={(event) => setToken(event.target.value)} />
            {connectionError && <p className="error" role="status">{connectionError}</p>}
            <div className="label-row"><label htmlFor="scenario">영상 대본</label><span>{scenario.length.toLocaleString()} / 20,000자</span></div>
            <textarea id="scenario" rows={13} maxLength={20_000} placeholder="영상에서 읽을 한국어 대본을 붙여넣으세요." value={scenario} onChange={(event) => setScenario(event.target.value)} />
            {estimateError && <p className="error" role="alert">{estimateError}</p>}
            {durationEstimate && <div className="duration-estimate">
              <strong aria-live="polite">{estimatedSeconds === null ? "읽을 문장 분석 중" : `예상 영상 길이 약 ${formatPlaybackDuration(estimatedSeconds)}`}</strong>
              {scriptEstimate ? <span>읽을 문장 {scriptEstimate.narrationChars.toLocaleString()}자 기준</span> : !hasNarrationLabels && <span>말하기 속도와 문장부호에 따라 약 {formatPlaybackDuration(durationEstimate.minSeconds)}~{formatPlaybackDuration(durationEstimate.maxSeconds)}</span>}
              <small>선택한 {narrationSpeed.toFixed(2)}배 속도 기준의 완성 영상 길이이며, 생성 소요시간이 아닙니다.</small>
              {overDurationLimit && <small role="alert">최대 {formatPlaybackDuration(maximumVideoSeconds)}를 넘습니다. 대본을 줄이거나 나레이션 속도를 높여 주세요.</small>}
              {timeWallet?.enabled && estimatedUsageSeconds !== null && <small>예상 사용 {formatPlaybackDuration(estimatedUsageSeconds)} · 제작 가능 {formatPlaybackDuration(timeWallet.availableSeconds ?? 0)}</small>}
              {insufficientTime && <small role="alert">제작 가능 시간이 부족합니다.</small>}
            </div>}
            {scriptEstimate?.narrationText && <details className="narration-preview">
              <summary>음성 대본 미리보기</summary>
              <p>{scriptEstimate.narrationText}</p>
            </details>}
            <div className="model-picker">
              <div className="narration-speed-control">
                <div className="label-row"><label htmlFor="narration-speed">나레이션 속도</label><strong>{narrationSpeed.toFixed(2)}배</strong></div>
                <input id="narration-speed" type="range" min="0.7" max="1.2" step="0.05" value={narrationSpeed} aria-valuetext={`${narrationSpeed.toFixed(2)}배`} onChange={(event) => setNarrationSpeed(Number(event.target.value))} />
                <div className="speed-scale" aria-hidden="true"><span>0.70배</span><span>0.85배</span><span>1.00배</span><span>1.20배</span></div>
              </div>
              {localGraphics || localIllustrations ? <p className="production-mode">제작 방식: {localGraphics ? "로컬 그래픽" : "로컬 도형 삽화 시험판"} · 한국어 음성 · 별도 이미지 API 호출 없음</p> : forcedLocalSlides && harnessId === "classic-slide" ? <p className="production-mode" role="status">이 시험 사이트에는 AI 장면 이미지가 연결되지 않았습니다. 아래 로컬 삽화 시험 옵션을 선택해야 제작할 수 있습니다.</p> : <>
                <label htmlFor="image-model">이미지 모델</label>
                <select id="image-model" value={imageModel} onChange={(event) => setImageModel(event.target.value as ImageModel)}>
                  {IMAGE_MODEL_OPTIONS.filter((option) => !productionMode?.supportedImageModels || productionMode.supportedImageModels.includes(option.value)).map((option) => <option key={option.value} value={option.value}>{option.label} — {productionMode?.imageProvider === "oauth" ? "구독 이미지 연결" : option.note}</option>)}
                </select>
              </>}
              {imageGenerationPaused && <p className="production-mode" role="status">구독 이미지 생성 한도에 도달했습니다. {new Date((productionMode?.imageGenerationPausedUntilUnix ?? 0) * 1000).toLocaleString("ko-KR", { timeZone: "Asia/Seoul" })} 이후 다시 시도해 주세요.</p>}
              <label htmlFor="creative-harness">영상 구성 방식</label>
              {optionsError && <div><p className="error" role="alert">{optionsError}</p><button type="button" className="secondary" onClick={() => setOptionsAttempt(value => value + 1)}>제작 설정 다시 불러오기</button></div>}
              <select id="creative-harness" disabled={!optionsReady} value={harnessId} onChange={(event) => setHarnessId(event.target.value)}>
                {!optionsReady && <option value={harnessId}>{optionsError ? "제작 설정 연결 실패" : "제작 설정 확인 중"}</option>}
                {optionsReady && harnesses.map(option => <option key={option.id} value={option.id}>{option.display_name} · {option.version}</option>)}
              </select>
              <fieldset className="style-options"><legend>영상 스타일</legend>
                {harnessId === "astra-motion" && MOTION_STYLE_OPTIONS.map((option) => <button key={option.value} type="button" className={motionStyleId === option.value ? "style-choice selected" : "style-choice"} aria-pressed={motionStyleId === option.value} onClick={() => setMotionStyleId(option.value)}>
                  <img src={option.preview} alt="" width="640" height="360" />
                  <strong>{option.label}</strong><small>{option.note}</small>
                </button>)}
                {IMAGE_STYLE_OPTIONS.filter((option) => harnessId === "astra-motion" ? harnesses.some(item => item.id === "classic-slide") && !forcedLocalSlides && CINEMATIC_STYLE_IDS.includes(option.value) : !forcedLocalSlides || option.value === "cute_character" || option.value === "fantasy_anime").map((option) => <button key={option.value} type="button" className={harnessId !== "astra-motion" && imageStyle === option.value ? "style-choice selected" : "style-choice"} aria-pressed={harnessId !== "astra-motion" && imageStyle === option.value} onClick={() => { if (harnessId === "astra-motion") setHarnessId("classic-slide"); setImageStyle(option.value); setLocalSlideImages(false); }}>
                  <img src={`/style-previews/${option.preview}.png`}
                    alt="" width="1280" height="720" />
                  <strong>{option.label}</strong><small>{option.note}{harnessId === "astra-motion" ? " · 슬라이드 연출" : ""}</small>
                </button>)}
              </fieldset>
              {harnessId === "classic-slide" && productionMode?.slideV05LocalImages && supportsLocalIllustrations && <label className="continuity-toggle">
                <input id="local-slide-images" type="checkbox" checked={localIllustrations} onChange={(event) => setLocalSlideImages(event.target.checked)} />
                <span><strong>로컬 도형 삽화 · 시험판</strong><small>대표 이미지는 화풍 참고용입니다. 이 옵션의 실제 영상은 간단한 도형 삽화이며 대표 이미지의 품질이나 화풍을 재현하지 않습니다.</small></span>
              </label>}
              {harnessId === "classic-slide" && productionMode?.slideV05LocalImages && <div className="music-controls">
                <label htmlFor="music-mode">배경음악</label>
                <select id="music-mode" value={musicMode} onChange={(event) => setMusicMode(event.target.value as "none" | "auto" | "upload")}>
                  <option value="none">없음</option><option value="auto">자동 음악</option><option value="upload">내 파일 사용</option>
                </select>
                {musicMode === "upload" && <>
                  <label htmlFor="music-file">음악 파일 · MP3, WAV, M4A, OGG · 최대 10MB</label>
                  <input id="music-file" type="file" accept="audio/mpeg,audio/wav,audio/mp4,audio/ogg,.mp3,.wav,.m4a,.ogg" onChange={(event) => { const file = event.target.files?.[0]; if (file) void uploadMusic(file); }} />
                  {musicUploadProgress !== null && <progress aria-label="배경음악 업로드" value={musicUploadProgress} max={100} />}
                  {musicUpload && <div className="music-upload-actions"><span>{musicUpload.name}</span><button type="button" className="secondary" onClick={() => void previewMusic()}>미리듣기</button><button type="button" className="secondary" onClick={() => void removeMusic()}>삭제</button></div>}
                  {musicPreviewUrl && <audio controls src={musicPreviewUrl} />}
                </>}
              </div>}
              <fieldset className="aspect-options"><legend>화면 비율</legend>
                <label><input type="radio" name="aspect-ratio" checked={aspectRatio === "16:9"} onChange={() => setAspectRatio("16:9")} /> 가로 16:9</label>
                <label><input type="radio" name="aspect-ratio" checked={aspectRatio === "9:16"} onChange={() => setAspectRatio("9:16")} /> 세로 9:16</label>
              </fieldset>
              <label className="continuity-toggle"><input type="checkbox" checked={subtitlesEnabled} onChange={(event) => setSubtitlesEnabled(event.target.checked)} /><span><strong>자막 포함</strong></span></label>
              {!localGraphics && !localIllustrations && <label className="continuity-toggle">
                <input type="checkbox" checked={continuityEnabled} onChange={(event) => setContinuityEnabled(event.target.checked)} />
                <span><strong>이미지 연속성 유지</strong><small>영상에 등장하는 주요 등장인물과 요소의 이미지를 일관되게 유지되도록 합니다. 추가 비용이 소모되고, 영상 생성시간이 늘어납니다.</small></span>
              </label>}
            </div>
              <div className="composer-footer">
              <div className="auto-features"><span>영상 한 편 최대 {formatPlaybackDuration(maximumVideoSeconds)}</span><span>자동 장면 설계</span><span>{videoKindLabel}</span></div>
              <button className="primary" onClick={() => void submit()} disabled={submitting}>{submitting ? "접수 중" : "영상 만들기"}</button>
            </div>
            {formError && <p className="error" role="alert">{formError}</p>}
          </section>

          {error && <p className="error" role="alert">{error}</p>}
          {job && (
            <section className="panel job-card">
              <div className="job-heading"><div><span className={`status ${job.status}`}>{statusLabel(job.status)}</span><h2>현재 작업</h2></div><code>{job.id}</code></div>
              <div className="progress-track"><span style={{ width: `${job.progress || 0}%` }} /></div>
              <div className="progress-copy"><strong>{stageLabel(job.currentStage ?? "queue_wait")}</strong><span>{job.progress || 0}%</span></div>
              {(job.status === "queued" || job.status === "waiting") && <div className="queue-copy">
                {job.queuePosition === null || job.queuePosition === undefined
                  ? <strong>대기 순서를 확인하는 중</strong>
                  : <strong>대기열 {job.queuePosition}번째 · {job.queuePosition === 1 && job.activeJobs === 1 ? "현재 작업이 끝나면 시작합니다" : `앞에 ${job.jobsAhead ?? 0}개 작업이 있습니다`}</strong>}
                {job.activeJobs !== null && job.activeJobs !== undefined && <span>현재 영상 {job.activeJobs}개 생성 중</span>}
              </div>}
              {job.status === "running" && <p className="queue-copy"><strong>생성 중 · 현재 작업을 처리하고 있습니다</strong></p>}
              {job.imageModel && !job.slideVisualProfile && job.motionStyle?.productionRoute !== "local_graphic" && productionMode?.imageProvider !== "local_graphic" && <p className="job-model">이미지 모델: <strong>{job.imageModel}</strong></p>}
              {job.motionStyle ? <p className="job-model">영상 스타일: <strong>{MOTION_STYLE_OPTIONS.find((option) => option.value === job.motionStyle?.id)?.label ?? job.motionStyle.id} · {job.motionStyle.version}</strong></p> : job.imageStyle && <p className="job-model">이미지 스타일: <strong>{IMAGE_STYLE_OPTIONS.find((option) => option.value === job.imageStyle)?.label ?? job.imageStyle}</strong></p>}
              {job.slideVisualProfile && <p className="job-model">장면 이미지: <strong>로컬 삽화 · {job.slideVisualProfile.version}</strong></p>}
              {job.musicSelection && job.musicSelection.mode !== "none" && <p className="job-model">배경음악: <strong>{job.musicSelection.mode === "auto" ? "자동 음악" : "업로드 파일"}</strong></p>}
              {job.harnessId && <p className="job-model">영상 연출: <strong>{job.harnessId}@{job.harnessVersion ?? "-"}</strong></p>}
              {job.episodeNumber && <p className="job-model">{job.durationProfile === "single_30m" ? "영상" : `에피소드 ${job.episodeNumber}`}: <strong>{job.episodeTitle ?? "제작 중"}</strong> · 최대 {job.durationProfile === "single_30m" ? "30분" : "60초"}</p>}
              {job.narrationSpeed && <p className="job-model">나레이션 속도: <strong>{Number(job.narrationSpeed).toFixed(2)}배</strong></p>}
              <p className="job-model">화면: <strong>{job.aspectRatio ?? "16:9"}</strong> · 자막: <strong>{job.subtitlesEnabled === false ? "없음" : "포함"}</strong></p>
              <p className="job-model">이미지 연속성: <strong>{job.continuityEnabled ? "ON" : "OFF"}</strong>{job.videoFps ? ` · ${job.videoFps}fps` : ""}</p>
              {job.error && <p className="error">{job.error}</p>}
              {job.status === "failed" && <button type="button" className="secondary" disabled={remaking} onClick={() => void remake()}>{remaking ? "접수 중" : "같은 설정으로 다시 만들기"}</button>}
              {job.status === "completed" && job.qualityGateStatus && <p className="job-model"><strong>{job.qualityGateStatus === "TECHNICAL_PASS_HUMAN_PENDING" ? "기술 검수 통과 · 디자인 검수 대기" : job.qualityGateStatus}</strong></p>}
              {job.status === "completed" && <VideoPreview key={`${job.id}:${token}`} jobId={job.id} api={api} />}
              {job.status === "completed" && <div className="result-actions">
                <button className="primary" onClick={download}>영상 받기</button>
                <button className="secondary" disabled={remaking} onClick={() => void remake()}>{remaking ? "접수 중" : "다시 만들기"}</button>
                {job.reviewStatus === "approved" ? <span className="review-result approved">승인됨</span> : job.reviewStatus === "revision_required" ? <span className="review-result revision">수정 필요</span> : <>
                  <button className="secondary" onClick={() => review("APPROVED")}>이 결과 승인</button>
                  <button className="secondary danger" onClick={() => review("REVISION_REQUIRED")}>수정 필요</button>
                </>}
              </div>}
            </section>
          )}
          {token && <section className="my-jobs" aria-labelledby="my-jobs-title">
            <div className="section-title"><h2 id="my-jobs-title">내 작업</h2><button type="button" className="secondary" onClick={() => void refreshMyJobs().catch(() => setConnectionError("작업 목록을 불러오지 못했습니다. 연결을 확인해 주세요."))}>새로고침</button></div>
            {myJobs.length === 0 ? <p>아직 만든 영상이 없습니다.</p> : <div className="my-jobs-list">
              {myJobs.map((item) => <button className="my-job-row" key={item.id} type="button" onClick={() => void selectMyJob(item.id)} aria-current={job?.id === item.id ? 'true' : undefined}>
                <JobThumbnail api={api} id={item.id} available={item.hasThumbnail} />
                <span className="my-job-text"><strong>{item.title}</strong><small>{new Date(item.queuedAt).toLocaleDateString('ko-KR')} · {item.videoDurationMs ? formatPlaybackDuration(Math.round(item.videoDurationMs / 1000)) : stageLabel(item.currentStage ?? undefined)}</small></span>
                <span className="my-job-status">{statusLabel(item.status)}{item.status === 'running' ? ` ${item.progress}%` : ''}</span>
              </button>)}
            </div>}
          </section>}
        </main>
      ) : (
        <main className="page admin-page">
          <div className="page-title">
            <div><p className="eyebrow">OPERATIONS</p><h1>{detailJobId ? "작업 상세" : adminView === "overview" ? "생성 현황과 비용" : adminView === "analytics" ? "개선 분석" : adminView === "prompts" ? "프롬프트 관리" : "모델 설정"}</h1></div>
            <div className="page-actions">
              {!detailJobId && <div className="admin-view-tabs" role="tablist" aria-label="관리자 화면">
                <button role="tab" aria-selected={adminView === "overview"} className={adminView === "overview" ? "active" : ""} onClick={() => setAdminView("overview")}>운영 현황</button>
                <button role="tab" aria-selected={adminView === "analytics"} className={adminView === "analytics" ? "active" : ""} onClick={() => setAdminView("analytics")}>개선 분석</button>
                <button role="tab" aria-selected={adminView === "prompts"} className={adminView === "prompts" ? "active" : ""} onClick={() => setAdminView("prompts")}>프롬프트</button>
                <button role="tab" aria-selected={adminView === "settings"} className={adminView === "settings" ? "active" : ""} onClick={() => setAdminView("settings")}>모델 설정</button>
              </div>}
              {!detailJobId && adminView === "overview" && <button className="secondary" onClick={refreshAdmin} disabled={adminLoading}>{adminLoading ? "불러오는 중" : "새로고침"}</button>}
            </div>
          </div>

          {adminView === "overview" ? <>
            {error && <p className="error" role="alert">{error}</p>}
            {!detailJobId && dashboard && <>
              <div className="section-tabs" role="tablist" aria-label="운영 현황 항목">
                <button role="tab" aria-selected={overviewSection === "jobs"} className={overviewSection === "jobs" ? "active" : ""} onClick={() => setOverviewSection("jobs")}>최근 영상</button>
                <button role="tab" aria-selected={overviewSection === "metrics"} className={overviewSection === "metrics" ? "active" : ""} onClick={() => setOverviewSection("metrics")}>운영 지표</button>
              </div>
              {overviewSection === "metrics" && <section className="metrics-grid">
                <Metric label="전체 영상" value={integer(dashboard.jobs.total)} suffix="개" />
                <Metric label="현재 작업" value={integer(dashboard.jobs.active)} suffix="개" />
                <Metric label="실행 중 영상" value={dashboard.queue.activeJobs === null ? "-" : `${integer(dashboard.queue.activeJobs)} / ${integer(dashboard.queue.globalConcurrency)}`} />
                <Metric label="대기 작업" value={dashboard.queue.queuedJobs === null ? "-" : integer(dashboard.queue.queuedJobs)} suffix={dashboard.queue.queuedJobs === null ? "" : "개"} note={`최장 대기 ${dashboard.queue.oldestWaitMs === null ? "-" : duration(dashboard.queue.oldestWaitMs)}`} />
                <Metric label="큐 대기 p50 / p95" value={`${dashboard.queue.queueWaitP50Ms === null ? "-" : duration(dashboard.queue.queueWaitP50Ms)} / ${dashboard.queue.queueWaitP95Ms === null ? "-" : duration(dashboard.queue.queueWaitP95Ms)}`} note="실제 BullMQ 실행 시작 기준" />
                <Metric label="평균 생성 시간" value={duration(dashboard.jobs.averageDurationMs)} />
                <Metric label="추정 외부 비용" value={won(dashboard.usage.actualCostKrw)} note="ElevenLabs API 정가 기준" />
                <Metric label="Codex API 예상 비용" value={won(dashboard.usage.codexApiEquivalentCostKrw)} note="구독 토큰을 API 단가로 환산" />
                <Metric label="이미지 API 예상 비용" value={won(dashboard.usage.imageApiEquivalentCostKrw)} note="현재 OAuth 청구와 별도" />
                <Metric label="전체 API 환산 비용" value={won(dashboard.usage.apiEquivalentCostKrw)} note="Codex + 이미지 + 음성" />
                <Metric label="생성 이미지" value={integer(dashboard.usage.images)} suffix="장" />
              </section>}

              {overviewSection === "jobs" && <section className="admin-columns">
                <div className="panel table-panel">
                  <div className="section-title"><h2>최근 영상</h2><span>{jobs.length}건</span></div>
                  <div className="table-scroll"><table><thead><tr><th>작업</th><th>상태</th><th>대기</th><th>Harness</th><th>이미지 모델</th><th>스타일</th><th>음성</th><th>구간</th><th>전체 생성시간</th><th>영상 1분당 생성시간</th><th>영상 1분당 비용</th><th>프롬프트</th><th>품질</th><th>다운로드</th></tr></thead><tbody>
                    {jobs.map((item) => <tr key={item.id} role="link" tabIndex={0} title="새 탭에서 작업 상세 열기" onClick={() => openDetailInNewTab(item.id)} onKeyDown={(event) => { if (event.key === "Enter") openDetailInNewTab(item.id); }}><td><code>{item.id.slice(0, 8)}</code></td><td><span className={`status ${item.status}`}>{statusLabel(item.status)}</span></td><td>{item.queuePosition ? `${item.queuePosition}번째` : item.queueWaitMs !== null && item.queueWaitMs !== undefined ? duration(item.queueWaitMs) : "-"}</td><td>{item.harnessId ? `${item.harnessId}@${item.harnessVersion ?? "-"}` : "legacy"}</td><td>{item.imageModel ?? "-"}</td><td>{item.imageStyle ?? "legacy"}</td><td>{item.voiceProvider ?? "legacy"} · {Number(item.narrationSpeed ?? 1).toFixed(2)}배</td><td>{stageLabel(item.currentStage)}</td><td>{duration(item.totalDurationMs)}</td><td>{item.generationTimePerVideoMinuteMs === null || item.generationTimePerVideoMinuteMs === undefined ? "-" : duration(item.generationTimePerVideoMinuteMs)}</td><td>{item.costPerVideoMinuteKrw === null || item.costPerVideoMinuteKrw === undefined ? "-" : won(item.costPerVideoMinuteKrw)}</td><td>{item.promptSetVersion ? `v${item.promptSetVersion}` : "-"}</td><td>{item.qualityScore === null || item.qualityScore === undefined ? "미평가" : `${Number(item.qualityScore).toFixed(0)}점`}</td><td>{item.status === "completed" ? <button className="secondary" onClick={(event) => { event.stopPropagation(); void downloadAdminJob(item.id); }}>MP4</button> : "-"}</td></tr>)}
                  </tbody></table></div>
                </div>
                <div className="panel stage-panel">
                  <div className="section-title"><h2>구간별 평균</h2><span>결정론적 계측</span></div>
                  <ul>{dashboard.stages.map((stage) => <li key={stage.stage}><span>{stageLabel(stage.stage)}</span><strong>{duration(stage.averageDurationMs)}</strong></li>)}</ul>
                </div>
              </section>}
            </>}

            {detail && <section className="panel detail-panel">
              <div className="section-title"><h2>작업 상세</h2><button className="icon-button" onClick={() => detailJobId ? window.close() : setDetail(null)} aria-label={detailJobId ? "상세 탭 닫기" : "닫기"}>×</button></div>
              {detail.job && typeof detail.job.id === "string" && detail.job.status === "completed" && (
                <button className="primary" onClick={() => void downloadAdminJob(String(detail.job?.id))}>MP4 내려받기</button>
              )}
              <div className="section-tabs detail-tabs" role="tablist" aria-label="작업 상세 항목">
                <button role="tab" aria-selected={detailSection === "summary"} className={detailSection === "summary" ? "active" : ""} onClick={() => setDetailSection("summary")}>요약</button>
                <button role="tab" aria-selected={detailSection === "pipeline"} className={detailSection === "pipeline" ? "active" : ""} onClick={() => setDetailSection("pipeline")}>파이프라인</button>
                <button role="tab" aria-selected={detailSection === "cost"} className={detailSection === "cost" ? "active" : ""} onClick={() => setDetailSection("cost")}>비용·호출</button>
              </div>
              {detailSection === "summary" && detail.job && <div className="job-metric-grid">
                <DetailMetric label="Creative Harness" value={`${String(detail.job.harness_id ?? "classic-slide")}@${String(detail.job.harness_version ?? "legacy")}`} note={`revision ${String(detail.job.harness_source_revision ?? "-")}`} />
                <DetailMetric label="나레이션 속도" value={`${Number(detail.job.narration_speed ?? 1).toFixed(2)}배`} note={`${String(detail.job.voice_provider ?? "legacy")} · ${String(detail.job.voice_model ?? "-")}`} />
                <DetailMetric label="Harness manifest" value={String(detail.job.harness_manifest_sha256 ?? "-").slice(0, 16)} note={`source ${String(detail.job.harness_source_sha256 ?? "-").slice(0, 16)}`} />
                <DetailMetric label="Harness config" value={String(detail.job.harness_config_sha256 ?? "-").slice(0, 16)} note={`image ${String(detail.job.harness_image_digest ?? "-")}`} />
              </div>}
              {detailSection === "summary" && detail.metrics && <>
                <div className="job-metric-grid">
                  <DetailMetric label="전체 생성시간" value={duration(detail.metrics.totalGenerationTimeMs)} note={`완성 영상 ${duration(detail.metrics.videoDurationMs)}`} />
                  <DetailMetric label="Codex 추론 토큰" value={integer(detail.metrics.codexReasoningTokens)} note={`입력 ${integer(detail.metrics.codexInputTokens)} · 출력 ${integer(detail.metrics.codexOutputTokens)}`} />
                  <DetailMetric label="이미지 생성 토큰" value={integer(detail.metrics.imageTokens)} note={`${detail.metrics.imageCount}장 · 장당 ${integer(detail.metrics.imageCount ? detail.metrics.imageTokens / detail.metrics.imageCount : 0)}`} />
                  <DetailMetric label="이미지 API 예상 비용" value={won(detail.metrics.imageApiEstimatedCostKrw)} note={`$${detail.metrics.imageApiEstimatedCostUsd.toFixed(4)} · ${detail.metrics.imageCount}장 · OAuth 실제 청구 0원`} />
                  <DetailMetric label="총 환산 비용" value={won(detail.metrics.totalCostKrw)} note={detail.metrics.costComplete ? `실결제 외부비용 ${won(detail.metrics.actualExternalCostKrw)}` : `확인 가능한 비용 합계 · 미측정 ${detail.metrics.unpricedEvents}건`} />
                  <DetailMetric label="추론 비용 / 영상 1분" value={nullableWon(detail.metrics.inferenceCostPerVideoMinuteKrw)} note={`${detail.metrics.model} · ${detail.metrics.effort}`} />
                  <DetailMetric label="이미지 API 예상 / 1장" value={nullableWon(detail.metrics.imageCostPerImageKrw)} note={detail.metrics.imageModel} />
                  <DetailMetric label="음성 비용 / 음성 1분" value={nullableWon(detail.metrics.voiceCostPerMinuteKrw)} note={detail.metrics.voiceModel} />
                  <DetailMetric label="총비용 / 영상 1분" value={nullableWon(detail.metrics.totalCostPerVideoMinuteKrw)} note={`프롬프트 ${detail.metrics.promptSetVersion ? `v${detail.metrics.promptSetVersion}` : "미기록"}`} />
                </div>
                <div className="detail-subsection"><div className="section-title"><h3>비용 구성</h3><span>금액과 전체 환산 비용 비중</span></div>
                  <CostDiagram inferenceCostKrw={detail.metrics.inferenceCostKrw} imageCostKrw={detail.metrics.imageCostKrw} voiceCostKrw={detail.metrics.voiceCostKrw} actualExternalCostKrw={detail.metrics.actualExternalCostKrw} />
                </div>
                <QualityEditor api={api} detail={detail} onSaved={(score, note) => setDetail((current) => current?.metrics ? { ...current, metrics: { ...current.metrics, qualityScore: score, qualityNote: note } } : current)} />
                <div className="detail-subsection"><div className="section-title"><h3>실제 작업 타임라인</h3><span>벽시계 기준 실행 순서와 병렬 구간</span></div>
                  <StageTimeline stages={detail.stages} renderSegments={detail.renderSegments} stageLabel={stageLabel} />
                </div>
                <div className="detail-subsection"><div className="section-title"><h3>구간별 실제 작업시간</h3><span>대기와 상위 관리 구간을 제외한 실행시간</span></div>
                  <ActiveStageTable stages={detail.stages} renderSegments={detail.renderSegments} stageLabel={stageLabel} />
                </div>
              </>}
              {detailSection === "pipeline" && <>
              <div className="detail-counts"><span>구간 {detail.stages.length}</span><span>외부 호출 {detail.usage.length}</span><span>파일 {detail.assets.length}</span><span>프롬프트 {detail.prompts.length}</span><span>이미지 태스크 {detail.imageTasks.length}</span><span>음성 태스크 {detail.voiceTasks.length}</span><span>렌더 구간 {detail.renderSegments.length}</span><span>이벤트 {detail.events.length}</span></div>
              {detail.job?.narrative_blueprint && typeof detail.job.narrative_blueprint === "object" ? <NarrativeHierarchy blueprint={detail.job.narrative_blueprint as Record<string, unknown>} /> : null}
              {detail.imageTasks.length > 0 && <div className="detail-subsection"><div className="section-title"><h3>이미지 태스크와 참조</h3><span>의존성·큐·재시도 영속 기록</span></div>
                <div className="table-scroll"><table><thead><tr><th>유형</th><th>장면/에셋</th><th>상태</th><th>스타일</th><th>부모 키컷</th><th>참조 순서</th><th>실제 파일 snapshot</th><th>모델</th><th>품질</th></tr></thead><tbody>{detail.imageTasks.map((task) => <tr key={String(task.image_task_id)}><td>{String(task.task_type)}</td><td>{String(task.scene_id ?? task.asset_id ?? "-")}</td><td>{String(task.status)}</td><td>{String(task.image_style ?? "-")}</td><td><code>{task.parent_keycut_task_id ? String(task.parent_keycut_task_id).slice(0, 8) : "-"}</code></td><td>{Array.isArray(task.reference_kinds) ? task.reference_kinds.join(" → ") : "-"}</td><td>{referenceSnapshot(detail.imageAttempts, task.image_task_id)}</td><td>{String(task.model)}</td><td>{String(task.quality)}</td></tr>)}</tbody></table></div>
              </div>}
              {detail.voiceTasks.length > 0 && <div className="detail-subsection"><div className="section-title"><h3>음성 태스크와 재사용</h3><span>설정 해시·큐·QC 영속 기록</span></div>
                <div className="table-scroll"><table><thead><tr><th>장면</th><th>상태</th><th>공급자</th><th>모델/voice</th><th>설정 해시</th><th>길이</th><th>음량</th></tr></thead><tbody>{detail.voiceTasks.map((task) => { const qc = (task.qc ?? {}) as Record<string, unknown>; return <tr key={String(task.voice_task_id)}><td>{String(task.scene_id)}</td><td>{String(task.status)}</td><td>{String(task.provider)}</td><td>{String(task.model)}</td><td><code>{String(task.settings_hash).slice(0, 10)}</code></td><td>{Number(qc.duration_seconds ?? 0).toFixed(2)}초</td><td>{String(qc.max_volume_db ?? "-")} dB</td></tr>; })}</tbody></table></div>
              </div>}
              {detail.renderSegments.length > 0 && <div className="detail-subsection"><div className="section-title"><h3>선행 렌더 구간</h3><span>준비·시작·완료 및 입력 해시</span></div>
                <div className="table-scroll"><table><thead><tr><th>구간</th><th>장면</th><th>상태</th><th>입력 해시</th><th>렌더 시간</th></tr></thead><tbody>{detail.renderSegments.map((segment) => <tr key={String(segment.id)}><td>{String(segment.segment_index)}</td><td>{String(segment.first_scene_id)}–{String(segment.last_scene_id)}</td><td>{String(segment.status)}</td><td><code>{String(segment.input_hash).slice(0, 10)}</code></td><td>{duration(segment.duration_ms)}</td></tr>)}</tbody></table></div>
              </div>}
              </>}
              {detailSection === "cost" && <>
              {detail.promptSet && <details className="job-prompt-set"><summary>비교용 프롬프트 묶음 v{detail.promptSet.version} 구성 <span>활성 문서 {detail.promptSet.manifest.length}개</span></summary><div>{detail.promptSet.manifest.map((prompt) => <span key={prompt.relativePath}><code>{prompt.relativePath}</code><b>v{prompt.version}</b><small>{prompt.sha256.slice(0, 10)}</small></span>)}</div></details>}
              {detail.job && typeof detail.job.id === "string" && <CodexTranscriptPanel api={api} jobId={detail.job.id} jobStatus={String(detail.job.status ?? "")} />}
              <div className="section-title"><h3>장면·호출별 토큰과 비용</h3><span>API 환산은 실제 API 사용 시 예상액</span></div>
              <div className="table-scroll"><table><thead><tr><th>장면</th><th>제공자</th><th>모델</th><th>effort</th><th>용도</th><th>입력 토큰</th><th>출력 토큰</th><th>추론 토큰</th><th>문자</th><th>현재 실비</th><th>API 사용 예상</th></tr></thead><tbody>
                {detail.usage.map((entry, index) => <tr key={index}><td>{String(entry.scene_id ?? "전체")}</td><td>{String(entry.provider ?? "-")}</td><td>{String(entry.model ?? "-")}</td><td>{usageEffort(entry)}</td><td>{stageLabel(typeof entry.stage === "string" ? entry.stage : undefined)}</td><td>{integer(entry.input_tokens)}</td><td>{integer(entry.output_tokens)}</td><td>{integer(entry.reasoning_tokens)}</td><td>{integer(entry.characters)}</td><td>{won(Number(entry.actual_cost_usd || 0) * Number(entry.exchange_rate_usd_krw || 0))}</td><td>{won(Number(entry.api_equivalent_cost_usd || 0) * Number(entry.exchange_rate_usd_krw || 0))}</td></tr>)}
              </tbody></table></div>
              </>}
            </section>}
          </> : adminView === "analytics" ? <AnalyticsDashboard api={api} /> : adminView === "prompts" ? <PromptManager api={api} /> : <div className="settings-workspace">
            <div className="section-tabs" role="tablist" aria-label="모델 설정 항목">
              <button role="tab" aria-selected={settingsSection === "codex"} className={settingsSection === "codex" ? "active" : ""} onClick={() => setSettingsSection("codex")}>Codex</button>
              <button role="tab" aria-selected={settingsSection === "voice"} className={settingsSection === "voice" ? "active" : ""} onClick={() => setSettingsSection("voice")}>음성</button>
              <button role="tab" aria-selected={settingsSection === "harness"} className={settingsSection === "harness" ? "active" : ""} onClick={() => setSettingsSection("harness")}>Creative Harness</button>
            </div>
            <div hidden={settingsSection !== "codex"}><ModelSettings api={api} /></div>
            <div hidden={settingsSection !== "voice"}><VoiceSettings api={api} /></div>
            <div hidden={settingsSection !== "harness"}><HarnessSettings api={api} /></div>
          </div>}
        </main>
      )}
    </div>
  );
}

function NarrativeHierarchy({ blueprint }: { blueprint: Record<string, unknown> }) {
  const sequences = Array.isArray(blueprint.sequences) ? blueprint.sequences as Array<Record<string, unknown>> : [];
  const groups = Array.isArray(blueprint.scene_groups) ? blueprint.scene_groups as Array<Record<string, unknown>> : [];
  const scenes = Array.isArray(blueprint.scenes) ? blueprint.scenes as Array<Record<string, unknown>> : [];
  const style = blueprint.style_bible && typeof blueprint.style_bible === "object" ? blueprint.style_bible as Record<string, unknown> : null;
  return <details className="job-prompt-set" open>
    <summary>이야기 계층과 Keycut snapshot <span>{sequences.length} sequences · {scenes.length} scenes</span></summary>
    <div className="detail-subsection">
      <p><strong>{String(blueprint.title ?? "-")}</strong> · master keycut <code>{String(blueprint.master_keycut_scene_id ?? "-")}</code></p>
      <p>핵심 질문: {String(blueprint.core_question ?? "-")}<br />주장: {String(blueprint.thesis ?? "-")}</p>
      {style && <p>Style Bible: <strong>{String(style.preset_id ?? "-")}</strong> · {String(style.medium_and_rendering ?? "-")}</p>}
      <div className="table-scroll"><table><thead><tr><th>Sequence</th><th>역할·목적</th><th>Keycut</th><th>Groups</th><th>Scenes</th></tr></thead><tbody>{sequences.map((sequence) => {
        const sequenceGroups = groups.filter((group) => group.sequence_id === sequence.id);
        const sequenceScenes = scenes.filter((scene) => scene.sequence_id === sequence.id);
        return <tr key={String(sequence.id)}><td><code>{String(sequence.id)}</code></td><td>{String(sequence.role_in_story)} · {String(sequence.purpose)}</td><td><code>{String(sequence.keycut_scene_id)}</code></td><td>{sequenceGroups.map((group) => String(group.id)).join(", ")}</td><td>{sequenceScenes.map((scene) => `${String(scene.id)}${scene.cut_role === "keycut" ? "★" : ""}`).join(", ")}</td></tr>;
      })}</tbody></table></div>
    </div>
  </details>;
}

function Metric({ label, value, suffix, note }: { label: string; value: string; suffix?: string; note?: string }) {
  return <article className="metric"><span>{label}</span><strong>{value}{suffix && <small>{suffix}</small>}</strong>{note && <em>{note}</em>}</article>;
}

const nullableWon = (value: number | null) => value === null ? "측정 불가" : won(value);
const referenceSnapshot = (attempts: Array<Record<string, unknown>>, taskId: unknown) => {
  const attempt = [...attempts].reverse().find((item) => item.image_task_id === taskId && Array.isArray(item.reference_snapshot));
  if (!attempt || !Array.isArray(attempt.reference_snapshot) || attempt.reference_snapshot.length === 0) return "-";
  return attempt.reference_snapshot.map((entry) => {
    const value = entry as Record<string, unknown>;
    return `${String(value.kind ?? "reference")}:${String(value.sha256 ?? "").slice(0, 8)}`;
  }).join(" → ");
};
const usageEffort = (entry: Record<string, unknown>) => {
  if (typeof entry.effort === "string" && entry.effort) return entry.effort;
  if (entry.raw_usage && typeof entry.raw_usage === "object" && "reasoning_effort" in entry.raw_usage) {
    return String((entry.raw_usage as Record<string, unknown>).reasoning_effort ?? "-");
  }
  return "-";
};

function DetailMetric({ label, value, note }: { label: string; value: string; note: string }) {
  return <article><span>{label}</span><strong>{value}</strong><small>{note}</small></article>;
}

function JobThumbnail({ api, id, available }: {
  api: (url: string, init?: RequestInit, authenticated?: boolean) => Promise<Response>;
  id: string;
  available: boolean;
}) {
  const [url, setUrl] = useState<string | null>(null);
  const element = useRef<HTMLSpanElement>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) { setVisible(true); observer.disconnect(); }
    }, { rootMargin: "100px" });
    if (element.current) observer.observe(element.current);
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    if (!available || !visible) return;
    let active = true;
    let objectUrl: string | null = null;
    void api(`/api/jobs/${id}/thumbnail`).then(async (response) => {
      if (!response.ok) return;
      const blob = await response.blob();
      if (!active) return;
      objectUrl = URL.createObjectURL(blob);
      setUrl(objectUrl);
    }).catch(() => undefined);
    return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [api, id, available, visible]);
  return <span ref={element} className="my-job-thumb">{url ? <img src={url} alt="" /> : '영상'}</span>;
}

function QualityEditor({ api, detail, onSaved }: { api: (url: string, init?: RequestInit, authenticated?: boolean) => Promise<Response>; detail: JobDetail; onSaved: (score: number, note: string | null) => void }) {
  const [score, setScore] = useState(() => detail.metrics?.qualityScore?.toString() ?? "");
  const [note, setNote] = useState(() => detail.metrics?.qualityNote ?? "");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  useEffect(() => { setScore(detail.metrics?.qualityScore?.toString() ?? ""); setNote(detail.metrics?.qualityNote ?? ""); setMessage(""); }, [detail.metrics?.jobId]);
  const numericScore = Number(score);
  async function save() {
    if (!detail.metrics || !Number.isFinite(numericScore) || numericScore < 0 || numericScore > 100) return;
    setSaving(true); setMessage("");
    const response = await api(`/api/admin/jobs/${detail.metrics.jobId}/quality`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ score: numericScore, note }) }, false);
    if (response.ok) { const saved = await response.json(); onSaved(Number(saved.qualityScore), saved.qualityNote ?? null); setMessage("품질 평가를 저장했습니다."); }
    else setMessage("품질 평가를 저장하지 못했습니다.");
    setSaving(false);
  }
  return <div className="quality-editor"><div><label htmlFor="quality-score">관리자 품질 점수</label><span>자동 검사로 판단하기 어려운 내용·연출 품질을 0–100점으로 기록합니다.</span></div><input id="quality-score" type="number" min="0" max="100" step="1" value={score} onChange={(event) => setScore(event.target.value)} placeholder="0–100" /><input aria-label="품질 평가 메모" value={note} onChange={(event) => setNote(event.target.value)} maxLength={1000} placeholder="품질 변화나 문제점 메모" /><button className="secondary" onClick={save} disabled={saving || !score || numericScore < 0 || numericScore > 100}>{saving ? "저장 중" : "평가 저장"}</button>{message && <small>{message}</small>}</div>;
}
