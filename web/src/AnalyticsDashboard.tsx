import { useCallback, useEffect, useState } from "react";

type AdminApi = (url: string, init?: RequestInit, authenticated?: boolean) => Promise<Response>;
type GroupBy = "promptVersion" | "model" | "effort" | "imageModel" | "imageStyle" | "imageQuality" | "imageConcurrency" | "referenceCount" | "continuityMode" | "voiceProvider" | "voiceModel" | "voiceConcurrency" | "fps" | "harnessVersion";

type ComparisonRow = {
  key: string;
  jobs: number;
  scoredJobs: number;
  incompleteCostJobs: number;
  averageQualityScore: number | null;
  averageGenerationTimeMs: number | null;
  averageVideoDurationMs: number | null;
  averageCodexReasoningTokens: number | null;
  averageImageTokensPerImage: number | null;
  averageImageApiCostPerVideoKrw: number | null;
  inferenceCostPerVideoMinuteKrw: number | null;
  imageCostPerImageKrw: number | null;
  voiceCostPerMinuteKrw: number | null;
  totalCostPerVideoMinuteKrw: number | null;
};

type AnalyticsResponse = {
  groupBy: GroupBy;
  rows: ComparisonRow[];
  dimensions: { promptVersions: number[]; models: string[]; efforts: string[]; imageModels: string[]; imageStyles: string[]; imageQualities: string[]; imageConcurrencies: string[]; referenceCounts: string[]; continuityModes: string[]; voiceProviders: string[]; voiceModels: string[]; voiceConcurrencies: string[]; fpsValues: string[]; harnessVersions: string[] };
};

type ImageQueueResponse = {
  configuredConcurrency: number;
  effectiveConcurrency: number;
  queueDepth: number;
  active: number;
  succeeded: number;
  failed: number;
  attempts: number;
  retries: number;
  rateLimited: number;
  failedAttempts: number;
  imagesPerMinute: number | null;
  providerP50Ms: number | null;
  providerP95Ms: number | null;
  queueP50Ms: number | null;
  queueP95Ms: number | null;
  unreferencedScenes: number;
  scenes: number;
  continuityAssets: number;
  slots: Array<{ slot_id: string; attempts: number; busyMs: number }>;
  breakdown: Array<{ taskType: string; tasks: number; succeeded: number; failed: number; providerMs: number }>;
  referenceDistribution: Array<{ referenceCount: number; scenes: number }>;
  timeline: Array<{ jobId: string; taskType: string; sceneId: string | null; assetId: string | null; attempt: number; slotId: string; status: string; startedAt: string; finishedAt: string | null; providerMs: number | null; queueWaitMs: number | null; effectiveConcurrency: number; referenceCount: number }>;
};

type VoiceQueueResponse = {
  configuredConcurrency: number; queueDepth: number; active: number; succeeded: number; failed: number;
  attempts: number; retries: number; failedAttempts: number; rateLimited: number;
  providerP50Ms: number | null; providerP95Ms: number | null; queueP50Ms: number | null; queueP95Ms: number | null;
  slots: Array<{ slot_id: string; attempts: number; busyMs: number }>;
  timeline: Array<{ jobId: string; sceneId: string; settingsHash: string; attempt: number; slotId: string; status: string; providerMs: number | null; queueWaitMs: number | null }>;
};

const GROUP_LABELS: Record<GroupBy, string> = {
  promptVersion: "프롬프트 버전",
  model: "Codex 모델",
  effort: "추론 effort",
  imageModel: "이미지 모델",
  imageStyle: "이미지 스타일",
  imageQuality: "이미지 품질",
  imageConcurrency: "이미지 동시성",
  referenceCount: "최대 참조 수",
  continuityMode: "이미지 연속성",
  voiceProvider: "음성 공급자",
  voiceModel: "음성 모델",
  voiceConcurrency: "음성 동시성",
  fps: "영상 FPS",
  harnessVersion: "Creative Harness",
};
const integer = (value: number | null) => value === null ? "측정 불가" : Math.round(value).toLocaleString("ko-KR");
const won = (value: number | null) => value === null ? "측정 불가" : `${value.toLocaleString("ko-KR", { maximumFractionDigits: 2, minimumFractionDigits: 0 })}원`;
const seconds = (value: number | null) => value === null ? "측정 불가" : `${(value / 1000).toFixed(1)}초`;

export function AnalyticsDashboard({ api }: { api: AdminApi }) {
  const [groupBy, setGroupBy] = useState<GroupBy>("promptVersion");
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [queue, setQueue] = useState<ImageQueueResponse | null>(null);
  const [voiceQueue, setVoiceQueue] = useState<VoiceQueueResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [response, queueResponse, voiceQueueResponse] = await Promise.all([
        api(`/api/admin/analytics?groupBy=${groupBy}`, undefined, false),
        api("/api/admin/image-queue", undefined, false),
        api("/api/admin/voice-queue", undefined, false),
      ]);
      if (!response.ok || !queueResponse.ok || !voiceQueueResponse.ok) throw new Error("분석 데이터를 불러오지 못했습니다.");
      setData(await response.json());
      setQueue(await queueResponse.json());
      setVoiceQueue(await voiceQueueResponse.json());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setLoading(false);
    }
  }, [api, groupBy]);

  useEffect(() => { void load(); }, [load]);
  const rows = data?.rows ?? [];

  return <section className="analytics-workspace">
    <div className="analytics-toolbar panel">
      <div><strong>개선 실험 비교</strong><span>같은 기준으로 정규화한 시간·토큰·비용과 관리자 품질 점수를 비교합니다.</span></div>
      <div className="comparison-tabs" role="tablist" aria-label="비교 기준">
        {(Object.keys(GROUP_LABELS) as GroupBy[]).map((key) => <button key={key} role="tab" aria-selected={groupBy === key} className={groupBy === key ? "active" : ""} onClick={() => setGroupBy(key)}>{GROUP_LABELS[key]}</button>)}
      </div>
      <button className="secondary" onClick={load} disabled={loading}>{loading ? "불러오는 중" : "새로고침"}</button>
    </div>
    <p className="measurement-note">실제 외부 서비스를 사용해 완료된 Live 영상만 비교하며 mock E2E 기록은 제외합니다. 현재 이미지는 ChatGPT OAuth를 사용하므로 이미지 실청구는 0원이며, 이미지 비용은 같은 토큰을 OpenAI Image API로 호출할 때의 예상액입니다. 총 환산 비용은 Codex API 예상·이미지 API 예상·ElevenLabs 비용의 합입니다.</p>
    {queue && <section className="panel comparison-table">
      <div className="section-title"><h2>전역 이미지 큐</h2><span>공유 슬롯 {queue.effectiveConcurrency} / {queue.configuredConcurrency}개</span></div>
      <div className="job-metric-grid">
        <article><span>대기 / 실행</span><strong>{queue.queueDepth} / {queue.active}</strong><small>모든 영상 합계</small></article>
        <article><span>공급자 시간 p50 / p95</span><strong>{seconds(queue.providerP50Ms)} / {seconds(queue.providerP95Ms)}</strong><small>시도별 측정</small></article>
        <article><span>큐 대기 p50 / p95</span><strong>{seconds(queue.queueP50Ms)} / {seconds(queue.queueP95Ms)}</strong><small>의존성 대기 제외</small></article>
        <article><span>재시도 / 429</span><strong>{queue.retries} / {queue.rateLimited}</strong><small>전체 {queue.attempts}회 시도</small></article>
        <article><span>이미지 처리량</span><strong>{queue.imagesPerMinute === null ? "측정 불가" : `${queue.imagesPerMinute.toFixed(2)}/분`}</strong><small>실패 시도 {queue.failedAttempts}</small></article>
        <article><span>기준 에셋</span><strong>{queue.continuityAssets}</strong><small>에셋당 기준 이미지 1장</small></article>
        <article><span>무참조 장면</span><strong>{queue.unreferencedScenes} / {queue.scenes}</strong><small>즉시 실행 가능한 장면</small></article>
      </div>
      <div className="table-scroll"><table><thead><tr><th>슬롯</th><th>시도</th><th>공급자 점유</th></tr></thead><tbody>{queue.slots.map((slot) => <tr key={slot.slot_id}><td>{slot.slot_id}</td><td>{slot.attempts}</td><td>{seconds(Number(slot.busyMs))}</td></tr>)}</tbody></table></div>
      <div className="table-scroll"><table><thead><tr><th>종류</th><th>태스크</th><th>성공 / 실패</th><th>공급자 시간</th></tr></thead><tbody>{queue.breakdown.map((item) => <tr key={item.taskType}><td>{item.taskType}</td><td>{item.tasks}</td><td>{item.succeeded} / {item.failed}</td><td>{seconds(Number(item.providerMs))}</td></tr>)}</tbody></table></div>
      <div className="table-scroll"><table><thead><tr><th>장면 참조 수</th><th>장면 수</th></tr></thead><tbody>{queue.referenceDistribution.map((item) => <tr key={item.referenceCount}><td>{item.referenceCount}</td><td>{item.scenes}</td></tr>)}</tbody></table></div>
      <div className="table-scroll"><table><thead><tr><th>최근 슬롯</th><th>작업</th><th>종류</th><th>참조</th><th>대기</th><th>공급자</th><th>결과</th></tr></thead><tbody>{queue.timeline.slice(0, 20).map((item, index) => <tr key={`${item.jobId}-${item.sceneId ?? item.assetId}-${item.attempt}-${index}`}><td>{item.slotId}</td><td>{item.jobId.slice(0, 8)}</td><td>{item.taskType}</td><td>{item.referenceCount}</td><td>{seconds(Number(item.queueWaitMs))}</td><td>{seconds(Number(item.providerMs))}</td><td>{item.status}</td></tr>)}</tbody></table></div>
    </section>}
    {voiceQueue && <section className="panel comparison-table">
      <div className="section-title"><h2>전역 음성 큐</h2><span>공유 슬롯 {voiceQueue.active} / {voiceQueue.configuredConcurrency}개</span></div>
      <div className="job-metric-grid">
        <article><span>대기 / 실행</span><strong>{voiceQueue.queueDepth} / {voiceQueue.active}</strong><small>모든 영상 합계</small></article>
        <article><span>공급자 시간 p50 / p95</span><strong>{seconds(voiceQueue.providerP50Ms)} / {seconds(voiceQueue.providerP95Ms)}</strong><small>시도별 측정</small></article>
        <article><span>큐 대기 p50 / p95</span><strong>{seconds(voiceQueue.queueP50Ms)} / {seconds(voiceQueue.queueP95Ms)}</strong><small>전역 슬롯 대기</small></article>
        <article><span>재시도 / 실패</span><strong>{voiceQueue.retries} / {voiceQueue.failedAttempts}</strong><small>전체 {voiceQueue.attempts}회 시도</small></article>
      </div>
      <div className="table-scroll"><table><thead><tr><th>슬롯</th><th>작업</th><th>장면</th><th>시도</th><th>대기</th><th>공급자</th><th>결과</th></tr></thead><tbody>{voiceQueue.timeline.slice(0, 20).map((item, index) => <tr key={`${item.jobId}-${item.sceneId}-${item.attempt}-${index}`}><td>{item.slotId}</td><td>{item.jobId.slice(0, 8)}</td><td>{item.sceneId}</td><td>{item.attempt}</td><td>{seconds(Number(item.queueWaitMs))}</td><td>{seconds(Number(item.providerMs))}</td><td>{item.status}</td></tr>)}</tbody></table></div>
    </section>}
    {error && <p className="error" role="alert">{error}</p>}
    {!loading && !rows.length && <div className="panel empty-state">완료된 영상의 측정 기록이 없습니다.</div>}
    {rows.length > 0 && <>
      <div className="chart-grid">
        <BarChart title="영상 1분당 총 환산 비용" subtitle="추론 + 이미지 + 음성" rows={rows} value={(row) => row.totalCostPerVideoMinuteKrw} format={won} />
        <BarChart title="영상 1분당 Codex 추론 비용" subtitle="구독 토큰의 API 가격 환산" rows={rows} value={(row) => row.inferenceCostPerVideoMinuteKrw} format={won} />
        <BarChart title="영상 1개당 이미지 API 예상 비용" subtitle="현재 OAuth 청구액과 별도" rows={rows} value={(row) => row.averageImageApiCostPerVideoKrw} format={won} />
        <BarChart title="이미지 1장당 API 예상 비용" subtitle="텍스트·참조 이미지·출력 이미지 토큰 포함" rows={rows} value={(row) => row.imageCostPerImageKrw} format={won} />
        <BarChart title="음성 1분당 비용" subtitle="ElevenLabs 실제 생성 길이 기준" rows={rows} value={(row) => row.voiceCostPerMinuteKrw} format={won} />
        <BarChart title="영상 1개 평균 생성시간" subtitle="대기열과 재시도 포함" rows={rows} value={(row) => row.averageGenerationTimeMs} format={seconds} />
        <BarChart title="평균 품질 점수" subtitle="관리자가 평가한 0–100점" rows={rows} value={(row) => row.averageQualityScore} format={(value) => value === null ? "미평가" : `${value.toFixed(1)}점`} fixedMax={100} />
      </div>
      <section className="panel comparison-table">
        <div className="section-title"><h2>{GROUP_LABELS[groupBy]}별 상세 수치</h2><span>{rows.length}개 비교군</span></div>
        {rows.some((row) => row.incompleteCostJobs > 0) && <p className="inline-warning">가격 또는 토큰을 제공하지 않은 과거 호출이 포함된 비교군은 확인 가능한 비용만 합산합니다.</p>}
        <div className="table-scroll"><table><thead><tr><th>비교군</th><th>영상</th><th>평균 생성시간</th><th>평균 추론 토큰</th><th>이미지당 토큰</th><th>추론/영상 1분</th><th>이미지 API/영상</th><th>이미지 API/장</th><th>음성/1분</th><th>총비용/영상 1분</th><th>품질</th></tr></thead><tbody>
          {rows.map((row) => <tr key={row.key}><td><strong>{row.key}</strong></td><td>{row.jobs}개</td><td>{seconds(row.averageGenerationTimeMs)}</td><td>{integer(row.averageCodexReasoningTokens)}</td><td>{integer(row.averageImageTokensPerImage)}</td><td>{won(row.inferenceCostPerVideoMinuteKrw)}</td><td>{won(row.averageImageApiCostPerVideoKrw)}</td><td>{won(row.imageCostPerImageKrw)}</td><td>{won(row.voiceCostPerMinuteKrw)}</td><td>{won(row.totalCostPerVideoMinuteKrw)}</td><td>{row.averageQualityScore === null ? "미평가" : `${row.averageQualityScore.toFixed(1)}점 (${row.scoredJobs})`}</td></tr>)}
        </tbody></table></div>
      </section>
    </>}
  </section>;
}

function BarChart({ title, subtitle, rows, value, format, fixedMax }: {
  title: string;
  subtitle: string;
  rows: ComparisonRow[];
  value: (row: ComparisonRow) => number | null;
  format: (value: number | null) => string;
  fixedMax?: number;
}) {
  const maximum = fixedMax ?? Math.max(1, ...rows.map((row) => value(row) ?? 0));
  return <article className="panel metric-chart">
    <header><h2>{title}</h2><span>{subtitle}</span></header>
    <div className="bar-list">{rows.map((row) => {
      const current = value(row);
      const width = current === null ? 0 : Math.max(2, Math.min(100, current / maximum * 100));
      return <div className="bar-row" key={row.key}>
        <div className="bar-copy"><strong title={row.key}>{row.key}</strong><span>{format(current)}</span></div>
        <div className="bar-track"><i style={{ width: `${width}%` }} /></div>
      </div>;
    })}</div>
  </article>;
}
