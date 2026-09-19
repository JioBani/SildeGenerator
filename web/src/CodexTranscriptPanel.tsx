import { useCallback, useEffect, useState } from "react";

type Api = (url: string, init?: RequestInit, authenticated?: boolean) => Promise<Response>;
type Attempt = {
  attempt: number;
  status?: string;
  model?: string;
  effort?: string;
  fast_mode_requested?: boolean;
  service_tier_requested?: string;
  service_tier_actual?: string | null;
  request_id?: string | null;
  started_at?: string;
  first_event_at?: string | null;
  first_output_at?: string | null;
  completed_at?: string | null;
  event_count?: number;
  error?: string | null;
  files: Record<string, number | null>;
};

const time = (value?: string | null) => value ? new Date(value).toLocaleString("ko-KR") : "대기 중";

export function CodexTranscriptPanel({ api, jobId, jobStatus }: { api: Api; jobId: string; jobStatus: string }) {
  const [attempts, setAttempts] = useState<Attempt[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [request, setRequest] = useState("");
  const [output, setOutput] = useState("");
  const [events, setEvents] = useState("");
  const [error, setError] = useState("");

  const file = useCallback(async (attempt: number, part: string) => {
    const response = await api(`/api/admin/jobs/${jobId}/codex-transcripts/${attempt}/${part}`, undefined, false);
    if (response.status === 404) return "";
    if (!response.ok) throw new Error(`트랜스크립트 ${part} 파일을 읽지 못했습니다.`);
    return response.text();
  }, [api, jobId]);

  const load = useCallback(async (preferred?: number | null) => {
    try {
      const response = await api(`/api/admin/jobs/${jobId}/codex-transcripts`, undefined, false);
      if (!response.ok) throw new Error("Codex 트랜스크립트 목록을 읽지 못했습니다.");
      const payload = await response.json() as { attempts: Attempt[] };
      setAttempts(payload.attempts);
      const attempt = preferred ?? selected ?? payload.attempts[0]?.attempt ?? null;
      setSelected(attempt);
      if (attempt !== null) {
        const [requestText, outputText] = await Promise.all([file(attempt, "request"), file(attempt, "output")]);
        setRequest(requestText);
        setOutput(outputText);
      }
      setError("");
    } catch (reason) { setError(reason instanceof Error ? reason.message : String(reason)); }
  }, [api, file, jobId, selected]);

  useEffect(() => { void load(); }, [jobId]);
  useEffect(() => {
    if (!["queued", "running", "waiting"].includes(jobStatus)) return;
    const timer = window.setInterval(() => void load(), 3000);
    return () => window.clearInterval(timer);
  }, [jobStatus, load]);

  async function choose(attempt: number) {
    setSelected(attempt);
    setEvents("");
    await load(attempt);
  }
  const current = attempts.find((attempt) => attempt.attempt === selected);
  return <div className="codex-transcript-panel">
    <div className="section-title"><div><h3>Codex 스트리밍 원문</h3><p>서버 작업 파일을 주문형으로 읽으며 DB에는 원문을 저장하지 않습니다.</p></div><button className="secondary" onClick={() => void load()}>새로고침</button></div>
    {error && <p className="error">{error}</p>}
    {!attempts.length ? <p className="empty-copy">이 작업에는 저장된 Codex 스트림이 없습니다.</p> : <>
      <div className="transcript-attempts">{attempts.map((attempt) => <button key={attempt.attempt} className={attempt.attempt === selected ? "active" : ""} onClick={() => void choose(attempt.attempt)}>시도 {attempt.attempt} · {attempt.status ?? "진행 중"}</button>)}</div>
      {current && <div className="transcript-meta">
        <span>모델 <b>{current.model}</b></span><span>effort <b>{current.effort}</b></span><span>Fast <b>{current.fast_mode_requested ? "요청함" : "요청 안 함"}</b></span><span>실제 tier <b>{current.service_tier_actual ?? "확인 중"}</b></span><span>이벤트 <b>{current.event_count ?? 0}개</b></span>
        <span>시작 <b>{time(current.started_at)}</b></span><span>첫 이벤트 <b>{time(current.first_event_at)}</b></span><span>첫 출력 <b>{time(current.first_output_at)}</b></span><span>완료 <b>{time(current.completed_at)}</b></span>
      </div>}
      {current?.error && <p className="error">{current.error}</p>}
      <details open><summary>실제 요청 원문 <small>{current?.files.request?.toLocaleString("ko-KR") ?? 0} bytes</small></summary><pre>{request || "아직 요청 파일이 없습니다."}</pre></details>
      <details open><summary>Codex 출력 원문 <small>{current?.files.output?.toLocaleString("ko-KR") ?? 0} bytes</small></summary><pre>{output || "아직 출력이 시작되지 않았습니다."}</pre></details>
      <details onToggle={(event) => { if ((event.currentTarget as HTMLDetailsElement).open && !events && selected !== null) void file(selected, "events").then(setEvents).catch((reason) => setError(String(reason))); }}><summary>SSE 이벤트 원본 JSONL <small>{current?.files.events?.toLocaleString("ko-KR") ?? 0} bytes</small></summary><pre>{events || "열면 서버에서 원본 이벤트 파일을 읽습니다."}</pre></details>
    </>}
  </div>;
}
