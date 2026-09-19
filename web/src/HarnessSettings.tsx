import { useEffect, useState } from "react";

type Api = (url: string, init?: RequestInit, authenticated?: boolean) => Promise<Response>;
type Harness = { id: string; version?: string; display_name?: string; description?: string; compatible: boolean; manifest_sha256?: string; source_sha256?: string; config_sha256?: string };

export function HarnessSettings({ api }: { api: Api }) {
  const [items, setItems] = useState<Harness[]>([]); const [error, setError] = useState("");
  useEffect(() => { void api("/api/admin/harnesses", undefined, false).then(async response => { const payload = await response.json(); if (!response.ok) throw new Error(payload.message ?? "Harness 목록을 불러오지 못했습니다."); setItems(payload); }).catch(reason => setError(reason instanceof Error ? reason.message : String(reason))); }, [api]);
  return <section className="panel model-settings-panel"><div className="section-title"><div><h2>설치된 Creative Harness</h2><p>빌드 시 고정된 신뢰 코드만 표시됩니다. 웹 업로드나 runtime 설치는 지원하지 않습니다.</p></div></div>
    {error && <p className="error">{error}</p>}
    <div className="table-scroll"><table><thead><tr><th>Harness</th><th>버전</th><th>호환</th><th>Manifest</th><th>Source</th><th>Config</th></tr></thead><tbody>{items.map(item => <tr key={item.id}><td><strong>{item.display_name ?? item.id}</strong><small>{item.id} · {item.description}</small></td><td>{item.version ?? "-"}</td><td>{item.compatible ? "정상" : "비호환"}</td><td><code>{item.manifest_sha256?.slice(0, 12) ?? "-"}</code></td><td><code>{item.source_sha256?.slice(0, 12) ?? "-"}</code></td><td><code>{item.config_sha256?.slice(0, 12) ?? "-"}</code></td></tr>)}</tbody></table></div>
  </section>;
}
