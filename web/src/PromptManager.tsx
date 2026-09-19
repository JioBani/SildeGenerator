import { useCallback, useEffect, useState } from "react";

type AdminApi = (url: string, init?: RequestInit, authenticated?: boolean) => Promise<Response>;

type PromptRecord = {
  id: string;
  relativePath: string;
  title: string;
  group: string;
  active: boolean;
  timing: string;
  condition: string;
  purpose: string;
  usedBy: string;
  requiredVariables: string[];
  exists: boolean;
  content: string;
  sha256: string | null;
  modifiedAt: string | null;
  version: number | null;
};

type PromptVersion = {
  version: number;
  sha256: string;
  content: string;
  createdAt: string;
  current: boolean;
};

const dateTime = (value: string | null) => value
  ? new Intl.DateTimeFormat("ko-KR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value))
  : "파일 없음";

async function errorMessage(response: Response) {
  const payload = await response.json().catch(() => ({}));
  if (Array.isArray(payload.message)) return payload.message.join(" ");
  return payload.message ?? payload.error ?? response.statusText;
}

export function PromptManager({ api }: { api: AdminApi }) {
  const [items, setItems] = useState<PromptRecord[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [versions, setVersions] = useState<PromptVersion[]>([]);

  const selected = items.find((item) => item.id === selectedId) ?? null;
  const dirty = Boolean(selected && draft !== selected.content);
  const missingVariables = selected?.requiredVariables.filter((variable) => !draft.includes(variable)) ?? [];

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const response = await api("/api/admin/prompts", undefined, false);
      if (!response.ok) throw new Error(await errorMessage(response));
      const records = await response.json() as PromptRecord[];
      setItems(records);
      setSelectedId(records[0]?.id ?? "");
      setDraft(records[0]?.content ?? "");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => { void load(); }, [load]);

  const loadVersions = useCallback(async (id: string) => {
    if (!id) return setVersions([]);
    const response = await api(`/api/admin/prompts/${id}/versions`, undefined, false);
    if (response.ok) setVersions(await response.json());
  }, [api]);

  useEffect(() => { void loadVersions(selectedId); }, [loadVersions, selectedId]);

  function select(item: PromptRecord) {
    setSelectedId(item.id);
    setDraft(item.content);
    setError("");
    setNotice("");
  }

  async function save() {
    if (!selected || !dirty || missingVariables.length) return;
    setSaving(true);
    setError("");
    setNotice("");
    try {
      const response = await api(`/api/admin/prompts/${selected.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: draft, expectedSha256: selected.sha256 }),
      }, false);
      if (!response.ok) throw new Error(await errorMessage(response));
      const saved = await response.json() as PromptRecord;
      setItems((current) => current.map((item) => item.id === saved.id ? saved : item));
      setDraft(saved.content);
      await loadVersions(saved.id);
      setNotice("저장했습니다. 저장 후 시작하는 작업부터 새 내용이 적용됩니다.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setSaving(false);
    }
  }

  async function restore(version: PromptVersion) {
    if (!selected || version.current || dirty) return;
    setSaving(true);
    setError("");
    setNotice("");
    try {
      const response = await api(`/api/admin/prompts/${selected.id}/versions/${version.version}/restore`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ expectedSha256: selected.sha256 }),
      }, false);
      if (!response.ok) throw new Error(await errorMessage(response));
      const saved = await response.json() as PromptRecord;
      setItems((current) => current.map((item) => item.id === saved.id ? saved : item));
      setDraft(saved.content);
      await loadVersions(saved.id);
      setNotice(`v${version.version} 내용을 현재본으로 복원했습니다. 동일한 내용은 같은 버전으로 집계됩니다.`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="prompt-workspace">
      <div className="prompt-notice">
        <div><strong>Markdown 원본을 직접 관리합니다.</strong><span>진행 중인 작업은 영향을 받지 않으며, 완료 작업에는 당시 내용과 해시가 계속 보관됩니다.</span></div>
        <button className="secondary" onClick={load} disabled={loading || saving}>{loading ? "불러오는 중" : "목록 새로고침"}</button>
      </div>

      {error && <p className="error" role="alert">{error}</p>}
      {notice && <p className="success" role="status">{notice}</p>}

      {!loading && <div className="prompt-layout">
        <aside className="panel prompt-list" aria-label="프롬프트 목록">
          <div className="section-title"><h2>프롬프트</h2><span>{items.length}개</span></div>
          {items.map((item) => (
            <button key={item.id} className={item.id === selectedId ? "selected" : ""} onClick={() => select(item)}>
              <span className="prompt-list-top"><b>{item.title}</b><em className={item.active ? "active" : "reserved"}>{item.active ? "사용 중" : "예약됨"}</em></span>
              <small>{item.group} · {item.relativePath}</small>
              <p>{item.purpose}</p>
            </button>
          ))}
        </aside>

        {selected && <article className="panel prompt-detail">
          <header className="prompt-detail-header">
            <div><span className="prompt-group">{selected.group}</span><h2>{selected.title}</h2><code>{selected.relativePath}</code></div>
            <div className="prompt-actions">
              <button className="secondary" onClick={() => setDraft(selected.content)} disabled={!dirty || saving}>변경 취소</button>
              <button className="primary" onClick={save} disabled={!dirty || saving || !draft.trim() || Boolean(missingVariables.length)}>{saving ? "저장 중" : "저장"}</button>
            </div>
          </header>

          <div className="prompt-usage-grid">
            <Info label="사용 시점" value={selected.timing} />
            <Info label="사용 조건" value={selected.condition} />
            <Info label="역할" value={selected.purpose} />
            <Info label="사용 주체" value={selected.usedBy} />
          </div>

          <div className="prompt-meta-row">
            <span>문서 버전 <strong>v{selected.version ?? "-"}</strong></span>
            <span>수정 {dateTime(selected.modifiedAt)}</span>
            <span>SHA-256 <code title={selected.sha256 ?? undefined}>{selected.sha256?.slice(0, 12) ?? "없음"}</code></span>
            <span>{draft.length.toLocaleString("ko-KR")}자</span>
            {dirty && <strong>저장되지 않은 변경</strong>}
          </div>

          {selected.requiredVariables.length > 0 && <div className="prompt-variables">
            <span>필수 변수</span>
            {selected.requiredVariables.map((variable) => <code className={missingVariables.includes(variable) ? "missing" : ""} key={variable}>{variable}</code>)}
          </div>}
          {missingVariables.length > 0 && <p className="inline-warning">필수 변수를 삭제하면 저장할 수 없습니다: {missingVariables.join(", ")}</p>}

          <details className="prompt-history">
            <summary>버전 기록 <span>{versions.length}개</span></summary>
            <div>{versions.map((version) => <article key={version.version}>
              <div><strong>v{version.version}</strong>{version.current && <em>현재</em>}<span>{dateTime(version.createdAt)}</span><code>{version.sha256.slice(0, 12)}</code></div>
              <button className="secondary" onClick={() => restore(version)} disabled={version.current || dirty || saving}>이 버전 복원</button>
            </article>)}</div>
            {dirty && <p>저장되지 않은 변경을 취소한 뒤 이전 버전을 복원할 수 있습니다.</p>}
          </details>

          <label htmlFor="prompt-content">Markdown 내용</label>
          <textarea id="prompt-content" className="prompt-editor" value={draft} onChange={(event) => { setDraft(event.target.value); setNotice(""); }} spellCheck={false} />
        </article>}
      </div>}
    </section>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return <div><span>{label}</span><p>{value}</p></div>;
}
