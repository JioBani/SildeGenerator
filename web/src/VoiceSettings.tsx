import { useEffect, useRef, useState } from "react";
import { switchVoiceProvider, type ProviderMemory, type VoiceProvider } from "./voice-settings-draft";

type Api = (url: string, init?: RequestInit, authenticated?: boolean) => Promise<Response>;
type Settings = {
  provider: VoiceProvider; model: string; voiceId: string; voiceName: string;
  rate?: string; pitch?: string; volume?: string;
  stability?: number; similarityBoost?: number; speed?: number;
  elevenLabsConfigured: boolean; updatedAt: string | null;
};

export function VoiceSettings({ api }: { api: Api }) {
  const [saved, setSaved] = useState<Settings | null>(null);
  const [draft, setDraft] = useState<Settings | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [sampleUrl, setSampleUrl] = useState("");
  const providerMemory = useRef<ProviderMemory>({});
  async function load() {
    setBusy(true); setError("");
    try {
      const response = await api("/api/admin/settings/voice", undefined, false);
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.message ?? "음성 설정을 불러오지 못했습니다.");
      providerMemory.current = { [payload.provider as VoiceProvider]: payload };
      setSaved(payload); setDraft(payload);
    } catch (reason) { setError(reason instanceof Error ? reason.message : String(reason)); }
    finally { setBusy(false); }
  }
  useEffect(() => { void load(); }, []);
  async function save() {
    if (!draft) return;
    setBusy(true); setError(""); setMessage("");
    try {
      const response = await api("/api/admin/settings/voice", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(draft) }, false);
      const payload = await response.json();
      if (!response.ok) throw new Error(Array.isArray(payload.message) ? payload.message.join(" ") : payload.message ?? "저장하지 못했습니다.");
      providerMemory.current = { [payload.provider as VoiceProvider]: payload };
      setSaved(payload); setDraft(payload); setMessage("저장했습니다. 새로 접수되는 작업부터 적용됩니다.");
    } catch (reason) { setError(reason instanceof Error ? reason.message : String(reason)); }
    finally { setBusy(false); }
  }
  async function sample() {
    if (!draft) return;
    const confirmCredit = draft.provider !== "elevenlabs" || window.confirm("ElevenLabs credit을 사용해 짧은 테스트 음성을 생성할까요?");
    if (!confirmCredit) return;
    setBusy(true); setError("");
    try {
      const response = await api("/api/admin/settings/voice/sample", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: "안녕하세요. 음성 설정을 확인합니다.", confirmCredit }) }, false);
      if (!response.ok) { const payload = await response.json(); throw new Error(payload.message ?? "음성 테스트에 실패했습니다."); }
      if (sampleUrl) URL.revokeObjectURL(sampleUrl);
      setSampleUrl(URL.createObjectURL(await response.blob()));
    } catch (reason) { setError(reason instanceof Error ? reason.message : String(reason)); }
    finally { setBusy(false); }
  }
  if (!draft) return <section className="panel model-settings-panel"><p>{busy ? "음성 설정을 불러오는 중입니다." : error}</p></section>;
  return <section className="panel model-settings-panel voice-settings-panel">
    <div className="section-title"><div><h2>음성 설정</h2><p>공급자와 세부 설정은 작업 접수 시 snapshot으로 고정됩니다.</p></div><button className="secondary" onClick={() => void load()} disabled={busy}>새로고침</button></div>
    {error && <p className="error" role="alert">{error}</p>}{message && <p className="success" role="status">{message}</p>}
    <div className="model-settings-grid">
      <label><span>음성 공급자</span><select value={draft.provider} onChange={(event) => { const switched = switchVoiceProvider(draft, event.target.value as VoiceProvider, providerMemory.current, saved); providerMemory.current = switched.memory; setDraft({ ...draft, ...switched.draft }); }}><option value="mock">무음 Mock</option><option value="microsoft_edge">Microsoft Edge 음성 — 무료 테스트, 온라인</option><option value="elevenlabs">ElevenLabs — 운영 품질, credit 사용</option></select><small>{draft.provider === "mock" ? "CI용 무음입니다." : draft.provider === "microsoft_edge" ? "API key 직접 과금은 없지만 온라인 Microsoft 서비스와 커뮤니티 client를 사용합니다. 오프라인 TTS가 아닙니다." : `credit을 소비합니다. API key ${draft.elevenLabsConfigured ? "설정됨" : "필요"}`}</small></label>
      {draft.provider === "microsoft_edge" && <><label><span>한국어 voice</span><select value={draft.voiceId} onChange={(event) => setDraft({ ...draft, voiceId: event.target.value, voiceName: event.target.value })}><option value="ko-KR-InJoonNeural">인준 (남성)</option><option value="ko-KR-SunHiNeural">선희 (여성)</option><option value="ko-KR-HyunsuMultilingualNeural">현수 다국어 (남성)</option></select></label><label><span>속도</span><input value={draft.rate ?? "-30%"} onChange={(event) => setDraft({ ...draft, rate: event.target.value })} /></label><label><span>Pitch</span><input value={draft.pitch ?? "+0Hz"} onChange={(event) => setDraft({ ...draft, pitch: event.target.value })} /></label><label><span>Volume</span><input value={draft.volume ?? "+0%"} onChange={(event) => setDraft({ ...draft, volume: event.target.value })} /></label></>}
      {draft.provider === "elevenlabs" && <><label><span>Voice ID</span><input value={draft.voiceId} onChange={(event) => setDraft({ ...draft, voiceId: event.target.value })} /></label><label><span>모델</span><input value={draft.model} onChange={(event) => setDraft({ ...draft, model: event.target.value })} /></label><label><span>Stability</span><input type="number" min="0" max="1" step="0.05" value={draft.stability ?? .6} onChange={(event) => setDraft({ ...draft, stability: Number(event.target.value) })} /></label><label><span>Similarity</span><input type="number" min="0" max="1" step="0.05" value={draft.similarityBoost ?? .6} onChange={(event) => setDraft({ ...draft, similarityBoost: Number(event.target.value) })} /></label><label><span>Speed</span><input type="number" min="0.7" max="1.2" step="0.05" value={draft.speed ?? .7} onChange={(event) => setDraft({ ...draft, speed: Number(event.target.value) })} /></label></>}
    </div>
    <div className="settings-actions"><button className="primary" onClick={() => void save()} disabled={busy}>{busy ? "처리 중" : "음성 설정 저장"}</button><button className="secondary" onClick={() => void sample()} disabled={busy}>테스트 문장 합성</button><button className="secondary" onClick={() => { if (saved) { providerMemory.current = { [saved.provider]: saved }; setDraft(saved); } }} disabled={busy}>변경 취소</button></div>
    {sampleUrl && <audio controls src={sampleUrl}>음성 미리듣기를 지원하지 않는 브라우저입니다.</audio>}
  </section>;
}
