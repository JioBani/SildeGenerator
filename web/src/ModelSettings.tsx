import { useEffect, useMemo, useState } from "react";

type Api = (url: string, init?: RequestInit, authenticated?: boolean) => Promise<Response>;
type Settings = {
  model: string;
  effort: string;
  fastMode: boolean;
  modelOptions: string[];
  effortOptions: string[];
  updatedAt: string | null;
};

export function ModelSettings({ api }: { api: Api }) {
  const [saved, setSaved] = useState<Settings | null>(null);
  const [draft, setDraft] = useState<Settings | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    setBusy(true);
    setError("");
    try {
      const response = await api("/api/admin/codex-settings", undefined, false);
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.message ?? "모델 설정을 불러오지 못했습니다.");
      setSaved(payload);
      setDraft(payload);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally { setBusy(false); }
  }

  useEffect(() => { void load(); }, []);
  const dirty = useMemo(() => saved && draft && (
    saved.model !== draft.model || saved.effort !== draft.effort || saved.fastMode !== draft.fastMode
  ), [draft, saved]);

  async function save() {
    if (!draft) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await api("/api/admin/codex-settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: draft.model, effort: draft.effort, fastMode: draft.fastMode }),
      }, false);
      const payload = await response.json();
      if (!response.ok) throw new Error(Array.isArray(payload.message) ? payload.message.join(" ") : payload.message ?? "저장하지 못했습니다.");
      setSaved(payload);
      setDraft(payload);
      setMessage("저장했습니다. 이후 접수되는 영상부터 새 설정이 적용됩니다.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally { setBusy(false); }
  }

  if (!draft) return <section className="panel model-settings-panel"><p>{busy ? "모델 설정을 불러오는 중입니다." : error}</p></section>;
  return <section className="panel model-settings-panel">
    <div className="section-title"><div><h2>Codex 생성 설정</h2><p>작업 접수 시 설정을 고정해 실행 중 변경의 영향을 받지 않습니다.</p></div><button className="secondary" onClick={() => void load()} disabled={busy}>새로고침</button></div>
    {error && <p className="error" role="alert">{error}</p>}
    {message && <p className="success" role="status">{message}</p>}
    <div className="model-settings-grid">
      <label><span>모델</span><select value={draft.model} onChange={(event) => setDraft({ ...draft, model: event.target.value })}>{draft.modelOptions.map((model) => <option key={model} value={model}>{model}</option>)}</select><small>장면 구조와 이미지 프롬프트를 설계합니다.</small></label>
      <label><span>Reasoning effort</span><select value={draft.effort} onChange={(event) => setDraft({ ...draft, effort: event.target.value })}>{draft.effortOptions.map((effort) => <option key={effort} value={effort}>{effort}</option>)}</select><small>높을수록 추론 시간과 토큰이 늘어날 수 있습니다.</small></label>
      <label className="fast-mode-control"><span>Fast 모드 요청</span><button type="button" role="switch" aria-checked={draft.fastMode} className={draft.fastMode ? "toggle active" : "toggle"} onClick={() => setDraft({ ...draft, fastMode: !draft.fastMode })}><i /><b>{draft.fastMode ? "요청" : "요청 안 함"}</b></button><small>Fast 호환 tier(priority)를 요청합니다. 구독 경로가 default로 처리할 수 있어 실제 tier는 작업 원문에서 별도로 확인합니다.</small></label>
    </div>
    <div className="settings-actions"><button className="primary" onClick={() => void save()} disabled={busy || !dirty}>{busy ? "저장 중" : "설정 저장"}</button><button className="secondary" onClick={() => { if (saved) setDraft(saved); setMessage(""); }} disabled={busy || !dirty}>변경 취소</button></div>
    <p className="settings-meta">현재 저장 시각: {saved?.updatedAt ? new Date(saved.updatedAt).toLocaleString("ko-KR") : "환경변수 기본값"}</p>
  </section>;
}
