import { useEffect, useState } from "react";

type Props = { jobId: string; api: (url: string, init?: RequestInit) => Promise<Response> };

// The parent keys this component by job and credential so stale media cannot cross jobs.
export function VideoPreview({ jobId, api }: Props) {
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    let objectUrl: string | undefined;
    setUrl(null);
    setError("");
    void (async () => {
      try {
        const response = await api(`/api/jobs/${jobId}/video`, { signal: controller.signal });
        if (!response.ok) throw new Error(response.status === 401 || response.status === 403
          ? "영상을 열 수 없습니다. 이 작업을 만든 접근 토큰을 확인해 주세요."
          : response.status === 404 || response.status === 410
            ? "영상 파일이 없거나 보존 기간이 지났습니다."
            : "영상을 불러오지 못했습니다. 다시 시도해 주세요.");
        if (!response.headers.get("content-type")?.startsWith("video/")) throw new Error("영상 대신 잘못된 응답을 받았습니다. 다시 시도해 주세요.");
        const blob = await response.blob();
        if (controller.signal.aborted) return;
        if (!blob.size) throw new Error("영상 파일이 비어 있습니다.");
        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      } catch (reason) {
        if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : "영상 연결이 끊어졌습니다.");
      }
    })();
    return () => { controller.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [api, jobId, attempt]);
  return <div aria-label="완성 영상">
    {!url && !error && <p role="status">영상을 불러오는 중입니다.</p>}
    {error && <div><p className="error" role="alert">{error}</p><button type="button" className="secondary" onClick={() => setAttempt(value => value + 1)}>영상 다시 불러오기</button></div>}
    {url && !error && <video className="episode-preview" controls preload="metadata" src={url}
      onError={() => setError("영상을 재생하지 못했습니다. 다시 불러오거나 영상 받기를 이용해 주세요.")} />}
  </div>;
}
