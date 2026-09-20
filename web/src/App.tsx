import { useCallback, useEffect, useMemo, useState } from "react";
import "./app.css";
import { PromptManager } from "./PromptManager";
import { AnalyticsDashboard } from "./AnalyticsDashboard";
import { CodexTranscriptPanel } from "./CodexTranscriptPanel";
import { ModelSettings } from "./ModelSettings";
import { VoiceSettings } from "./VoiceSettings";
import { HarnessSettings } from "./HarnessSettings";
import { StageTimeline } from "./StageTimeline";
import { estimateNarrationDuration, formatPlaybackDuration } from "./duration-estimate";

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
  continuityEnabled?: boolean;
  videoFps?: number;
  voiceConcurrency?: number;
  voiceProvider?: string | null;
  voiceModel?: string | null;
  voiceId?: string | null;
  harnessId?: string | null;
  harnessVersion?: string | null;
  queuePosition?: number | null;
  jobsAhead?: number | null;
  activeJobs?: number | null;
  queuedJobs?: number | null;
  queueWaitMs?: number | string | null;
  generationTimePerVideoMinuteMs?: number | string | null;
  costPerVideoMinuteKrw?: number | string | null;
};

type ImageModel = "gpt-image-2" | "gpt-image-2.5-sunburst" | "gpt-image-2.5-flare";
type ImageStyle = "editorial_illustration" | "cinematic_realism" | "graphic_explainer";
type HarnessOption = { id: string; version: string; display_name: string; description: string; compatible: boolean; public: boolean };

const IMAGE_MODEL_OPTIONS: Array<{ value: ImageModel; label: string; note: string }> = [
  { value: "gpt-image-2", label: "GPT Image 2", note: "낮은 API 단가" },
  { value: "gpt-image-2.5-sunburst", label: "GPT Image 2.5 Sunburst", note: "최고 품질 · 기본값" },
  { value: "gpt-image-2.5-flare", label: "GPT Image 2.5 Flare", note: "빠른 2.5" },
];
const IMAGE_STYLE_OPTIONS: Array<{ value: ImageStyle; label: string; note: string }> = [
  { value: "editorial_illustration", label: "에디토리얼 일러스트", note: "정교한 편집 일러스트와 절제된 상징" },
  { value: "cinematic_realism", label: "영화적 사실주의", note: "영화 스틸 같은 인물·공간·조명" },
  { value: "graphic_explainer", label: "그래픽 설명", note: "인과와 구조를 명료한 도형·공간으로 설명" },
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
  const [tab, setTab] = useState<"create" | "admin">(() => detailJobId ? "admin" : "create");
  const [adminView, setAdminView] = useState<"overview" | "analytics" | "prompts" | "settings">("overview");
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) ?? "");
  const [scenario, setScenario] = useState("");
  const [imageModel, setImageModel] = useState<ImageModel>("gpt-image-2.5-sunburst");
  const [imageStyle, setImageStyle] = useState<ImageStyle>("editorial_illustration");
  const [continuityEnabled, setContinuityEnabled] = useState(false);
  const [harnessId, setHarnessId] = useState("classic-slide");
  const [harnesses, setHarnesses] = useState<HarnessOption[]>([]);
  const [job, setJob] = useState<JobStatus | null>(null);
  const [error, setError] = useState("");
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [jobs, setJobs] = useState<JobStatus[]>([]);
  const [detail, setDetail] = useState<JobDetail | null>(null);
  const [adminLoading, setAdminLoading] = useState(false);
  const [restorePending, setRestorePending] = useState(true);
  const durationEstimate = useMemo(() => estimateNarrationDuration(scenario), [scenario]);

  useEffect(() => localStorage.setItem(TOKEN_KEY, token), [token]);

  useEffect(() => { void fetch(API_BASE + "/api/jobs/options/harnesses").then(response => response.ok ? response.json() : []).then(items => setHarnesses(items.filter((item: HarnessOption) => item.compatible && item.public))).catch(() => setHarnesses([])); }, []);

  const api = useCallback((url: string, init?: RequestInit, authenticated = true) => {
    const headers = new Headers(init?.headers);
    if (authenticated && token) headers.set("Authorization", `Bearer ${token}`);
    return fetch(API_BASE + url, { ...init, headers });
  }, [token]);

  useEffect(() => {
    if (!restorePending || !token || job) return;
    const id = localStorage.getItem(RECENT_JOB_KEY);
    if (!id) { setRestorePending(false); return; }
    void api(`/api/jobs/${id}`).then(async (response) => {
      if (response.ok) setJob(await response.json());
      else if ([401, 404, 410].includes(response.status)) localStorage.removeItem(RECENT_JOB_KEY);
    }).finally(() => setRestorePending(false));
  }, [api, job, restorePending, token]);

  useEffect(() => {
    if (!job || ["completed", "failed"].includes(job.status)) return;
    const timer = window.setTimeout(async () => {
      const response = await api(`/api/jobs/${job.id}`);
      if (response.ok) setJob(await response.json());
    }, 2_000);
    return () => window.clearTimeout(timer);
  }, [api, job]);

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
    const response = await api("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario, imageModel, imageStyle, continuityEnabled, harnessId }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      setError(payload.message ?? payload.error ?? response.statusText);
      return;
    }
    localStorage.setItem(RECENT_JOB_KEY, payload.id);
    // The worker can claim the first job immediately after POST, making the
    // creation-time position stale before it is painted. Show the explicit
    // checking state until the first authoritative 2-second status poll.
    setJob({ ...payload, queuePosition: null, jobsAhead: null });
  }

  async function downloadJob(id: string) {
    const response = await api(`/api/jobs/${id}/video`);
    if (!response.ok) return setError("완성 영상을 내려받지 못했습니다. 이 작업을 만든 접근 토큰인지 확인해 주세요.");
    await saveVideo(response, id);
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
    URL.revokeObjectURL(url);
  }

  async function download() {
    if (job) await downloadJob(job.id);
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
          <section className="hero">
            <p className="eyebrow">NARRATED SLIDE VIDEO</p>
            <h1>대본 하나로 완성하는<br />슬라이드 영상</h1>
            <p>장면 구성, 이미지, 한국어 음성, 자막과 전환 효과를 자동으로 만듭니다.</p>
          </section>

          <section className="panel composer">
            <label htmlFor="token">접근 토큰</label>
            <input id="token" type="password" autoComplete="off" placeholder="관리자가 발급한 토큰" value={token} onChange={(event) => setToken(event.target.value)} />
            <div className="label-row"><label htmlFor="scenario">영상 대본</label><span>{scenario.length.toLocaleString()} / 20,000자</span></div>
            <textarea id="scenario" rows={13} maxLength={20_000} placeholder="영상에서 읽을 한국어 대본을 붙여넣으세요." value={scenario} onChange={(event) => setScenario(event.target.value)} />
            {durationEstimate && <div className="duration-estimate">
              <strong aria-live="polite">예상 영상 길이 약 {formatPlaybackDuration(durationEstimate.centerSeconds)}</strong>
              <span>말하기 속도와 문장부호에 따라 약 {formatPlaybackDuration(durationEstimate.minSeconds)}~{formatPlaybackDuration(durationEstimate.maxSeconds)}</span>
              <small>현재 한국어 음성 설정 기준의 완성 영상 재생시간이며, 생성 소요시간이 아닙니다.</small>
            </div>}
            <div className="model-picker">
              <label htmlFor="image-model">이미지 모델</label>
              <select id="image-model" value={imageModel} onChange={(event) => setImageModel(event.target.value as ImageModel)}>
                {IMAGE_MODEL_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label} — {option.note}</option>)}
              </select>
              <label htmlFor="image-style">이미지 스타일</label>
              <select id="image-style" value={imageStyle} onChange={(event) => setImageStyle(event.target.value as ImageStyle)}>
                {IMAGE_STYLE_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label} · {option.note}</option>)}
              </select>
              <label htmlFor="creative-harness">영상 연출 Harness</label>
              <select id="creative-harness" value={harnessId} onChange={(event) => setHarnessId(event.target.value)}>
                {(harnesses.length ? harnesses : [{ id: "classic-slide", version: "1.0.0", display_name: "기본 슬라이드 연출", description: "", compatible: true, public: true }]).map(option => <option key={option.id} value={option.id}>{option.display_name} · {option.version}</option>)}
              </select>
              <label className="continuity-toggle">
                <input type="checkbox" checked={continuityEnabled} onChange={(event) => setContinuityEnabled(event.target.checked)} />
                <span><strong>이미지 연속성 유지</strong><small>반복되는 인물·사물에 기준 이미지를 사용합니다. 기본값은 OFF입니다.</small></span>
              </label>
              <small>영상 작업이 시작되면 선택한 모델이 해당 작업의 기준 에셋과 모든 장면에 고정됩니다.</small>
            </div>
            <div className="composer-footer">
              <div className="auto-features"><span>자동 장면 분할</span><span>자동 길이 조절</span><span>Ken Burns + 크로스페이드</span></div>
              <button className="primary" onClick={submit} disabled={!scenario.trim() || !token || Boolean(job && !["completed", "failed"].includes(job.status))}>영상 만들기</button>
            </div>
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
              {job.imageModel && <p className="job-model">이미지 모델: <strong>{job.imageModel}</strong></p>}
              {job.imageStyle && <p className="job-model">이미지 스타일: <strong>{IMAGE_STYLE_OPTIONS.find((option) => option.value === job.imageStyle)?.label ?? job.imageStyle}</strong></p>}
              {job.harnessId && <p className="job-model">영상 연출: <strong>{job.harnessId}@{job.harnessVersion ?? "-"}</strong></p>}
              <p className="job-model">이미지 연속성: <strong>{job.continuityEnabled ? "ON" : "OFF"}</strong>{job.videoFps ? ` · ${job.videoFps}fps` : ""}</p>
              {job.error && <p className="error">{job.error}</p>}
              {job.status === "completed" && <button className="primary" onClick={download}>MP4 내려받기</button>}
            </section>
          )}
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
              <section className="metrics-grid">
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
              </section>

              <section className="admin-columns">
                <div className="panel table-panel">
                  <div className="section-title"><h2>최근 영상</h2><span>{jobs.length}건</span></div>
                  <div className="table-scroll"><table><thead><tr><th>작업</th><th>상태</th><th>대기</th><th>Harness</th><th>이미지 모델</th><th>스타일</th><th>음성</th><th>구간</th><th>전체 생성시간</th><th>영상 1분당 생성시간</th><th>영상 1분당 비용</th><th>프롬프트</th><th>품질</th><th>다운로드</th></tr></thead><tbody>
                    {jobs.map((item) => <tr key={item.id} role="link" tabIndex={0} title="새 탭에서 작업 상세 열기" onClick={() => openDetailInNewTab(item.id)} onKeyDown={(event) => { if (event.key === "Enter") openDetailInNewTab(item.id); }}><td><code>{item.id.slice(0, 8)}</code></td><td><span className={`status ${item.status}`}>{statusLabel(item.status)}</span></td><td>{item.queuePosition ? `${item.queuePosition}번째` : item.queueWaitMs !== null && item.queueWaitMs !== undefined ? duration(item.queueWaitMs) : "-"}</td><td>{item.harnessId ? `${item.harnessId}@${item.harnessVersion ?? "-"}` : "legacy"}</td><td>{item.imageModel ?? "-"}</td><td>{item.imageStyle ?? "legacy"}</td><td>{item.voiceProvider ?? "legacy"}</td><td>{stageLabel(item.currentStage)}</td><td>{duration(item.totalDurationMs)}</td><td>{item.generationTimePerVideoMinuteMs === null || item.generationTimePerVideoMinuteMs === undefined ? "-" : duration(item.generationTimePerVideoMinuteMs)}</td><td>{item.costPerVideoMinuteKrw === null || item.costPerVideoMinuteKrw === undefined ? "-" : won(item.costPerVideoMinuteKrw)}</td><td>{item.promptSetVersion ? `v${item.promptSetVersion}` : "-"}</td><td>{item.qualityScore === null || item.qualityScore === undefined ? "미평가" : `${Number(item.qualityScore).toFixed(0)}점`}</td><td>{item.status === "completed" ? <button className="secondary" onClick={(event) => { event.stopPropagation(); void downloadAdminJob(item.id); }}>MP4</button> : "-"}</td></tr>)}
                  </tbody></table></div>
                </div>
                <div className="panel stage-panel">
                  <div className="section-title"><h2>구간별 평균</h2><span>결정론적 계측</span></div>
                  <ul>{dashboard.stages.map((stage) => <li key={stage.stage}><span>{stageLabel(stage.stage)}</span><strong>{duration(stage.averageDurationMs)}</strong></li>)}</ul>
                </div>
              </section>
            </>}

            {detail && <section className="panel detail-panel">
              <div className="section-title"><h2>작업 상세</h2><button className="icon-button" onClick={() => detailJobId ? window.close() : setDetail(null)} aria-label={detailJobId ? "상세 탭 닫기" : "닫기"}>×</button></div>
              {detail.job && typeof detail.job.id === "string" && detail.job.status === "completed" && (
                <button className="primary" onClick={() => void downloadAdminJob(String(detail.job?.id))}>MP4 내려받기</button>
              )}
              {detail.job && <div className="job-metric-grid">
                <DetailMetric label="Creative Harness" value={`${String(detail.job.harness_id ?? "classic-slide")}@${String(detail.job.harness_version ?? "legacy")}`} note={`revision ${String(detail.job.harness_source_revision ?? "-")}`} />
                <DetailMetric label="Harness manifest" value={String(detail.job.harness_manifest_sha256 ?? "-").slice(0, 16)} note={`source ${String(detail.job.harness_source_sha256 ?? "-").slice(0, 16)}`} />
                <DetailMetric label="Harness config" value={String(detail.job.harness_config_sha256 ?? "-").slice(0, 16)} note={`image ${String(detail.job.harness_image_digest ?? "-")}`} />
              </div>}
              {detail.metrics && <>
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
                <QualityEditor api={api} detail={detail} onSaved={(score, note) => setDetail((current) => current?.metrics ? { ...current, metrics: { ...current.metrics, qualityScore: score, qualityNote: note } } : current)} />
                <div className="detail-subsection"><div className="section-title"><h3>실제 작업 타임라인</h3><span>벽시계 기준 실행 순서와 병렬 구간</span></div>
                  <StageTimeline stages={detail.stages} summaries={detail.metrics.stages} stageLabel={stageLabel} />
                </div>
                <div className="detail-subsection"><div className="section-title"><h3>구간별 생성시간</h3><span>실제 경과와 병렬 작업 누적시간을 분리</span></div>
                  <div className="table-scroll"><table><thead><tr><th>구간</th><th>작업 수</th><th>실제 경과시간</th><th>병렬 작업 누적시간</th><th>장/회당 평균</th></tr></thead><tbody>{detail.metrics.stages.map((stage) => { const imageStage = ["image_generation", "keycut_generation", "continuity_asset_generation"].includes(stage.stage); return <tr key={stage.stage}><td>{stageLabel(stage.stage)}</td><td>{stage.runs}{imageStage ? "장" : "회"}</td><td><strong>{duration(stage.wallClockDurationMs)}</strong></td><td>{duration(stage.totalDurationMs)}</td><td>{duration(stage.averageDurationMs)}</td></tr>; })}</tbody></table></div>
                </div>
              </>}
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
              {detail.promptSet && <details className="job-prompt-set"><summary>비교용 프롬프트 묶음 v{detail.promptSet.version} 구성 <span>활성 문서 {detail.promptSet.manifest.length}개</span></summary><div>{detail.promptSet.manifest.map((prompt) => <span key={prompt.relativePath}><code>{prompt.relativePath}</code><b>v{prompt.version}</b><small>{prompt.sha256.slice(0, 10)}</small></span>)}</div></details>}
              {detail.job && typeof detail.job.id === "string" && <CodexTranscriptPanel api={api} jobId={detail.job.id} jobStatus={String(detail.job.status ?? "")} />}
              <div className="section-title"><h3>장면·호출별 토큰과 비용</h3><span>API 환산은 실제 API 사용 시 예상액</span></div>
              <div className="table-scroll"><table><thead><tr><th>장면</th><th>제공자</th><th>모델</th><th>effort</th><th>용도</th><th>입력 토큰</th><th>출력 토큰</th><th>추론 토큰</th><th>문자</th><th>현재 실비</th><th>API 사용 예상</th></tr></thead><tbody>
                {detail.usage.map((entry, index) => <tr key={index}><td>{String(entry.scene_id ?? "전체")}</td><td>{String(entry.provider ?? "-")}</td><td>{String(entry.model ?? "-")}</td><td>{usageEffort(entry)}</td><td>{stageLabel(typeof entry.stage === "string" ? entry.stage : undefined)}</td><td>{integer(entry.input_tokens)}</td><td>{integer(entry.output_tokens)}</td><td>{integer(entry.reasoning_tokens)}</td><td>{integer(entry.characters)}</td><td>{won(Number(entry.actual_cost_usd || 0) * Number(entry.exchange_rate_usd_krw || 0))}</td><td>{won(Number(entry.api_equivalent_cost_usd || 0) * Number(entry.exchange_rate_usd_krw || 0))}</td></tr>)}
              </tbody></table></div>
            </section>}
          </> : adminView === "analytics" ? <AnalyticsDashboard api={api} /> : adminView === "prompts" ? <PromptManager api={api} /> : <div className="settings-workspace"><ModelSettings api={api} /><VoiceSettings api={api} /><HarnessSettings api={api} /></div>}
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
