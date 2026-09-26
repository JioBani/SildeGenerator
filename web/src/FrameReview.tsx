import { useEffect, useRef, useState } from 'react';
import './frame-review.css';

type Frames = Record<string, string>;
export function FrameReview() {
  const [baseline, setBaseline] = useState<Frames>({});
  const [candidate, setCandidate] = useState<Frames>({});
  const [index, setIndex] = useState(0);
  const [status, setStatus] = useState('프레임 파일을 선택하세요');
  const [ready, setReady] = useState(false);
  const canvas = useRef<HTMLCanvasElement>(null);
  const urls = useRef<string[]>([]);
  const names = [...new Set([...Object.keys(baseline), ...Object.keys(candidate)])].sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
  const name = names[index];
  useEffect(() => () => urls.current.forEach(URL.revokeObjectURL), []);
  function load(files: FileList | null, setter: (value: Frames) => void) {
    const frames: Frames = {};
    for (const file of Array.from(files ?? [])) {
      if (!file.type.startsWith('image/')) continue;
      const url = URL.createObjectURL(file);
      urls.current.push(url);
      frames[file.name] = url;
    }
    setter(frames);
    setIndex(0);
  }
  useEffect(() => {
    let active = true;
    setReady(false);
    const context = canvas.current?.getContext('2d');
    context?.clearRect(0, 0, canvas.current!.width, canvas.current!.height);
    if (!name || !baseline[name] || !candidate[name]) {
      setStatus(name ? '대응 프레임 누락' : '프레임 파일을 선택하세요');
      return;
    }
    const decode = (src: string) => new Promise<HTMLImageElement>((resolve, reject) => {
      const img = new Image(); img.onload = () => resolve(img); img.onerror = reject; img.src = src;
    });
    Promise.all([decode(baseline[name]), decode(candidate[name])]).then(([a, b]) => {
      if (!active || !canvas.current || !context) return;
      if (a.naturalWidth !== b.naturalWidth || a.naturalHeight !== b.naturalHeight) {
        setStatus('이미지 크기 불일치'); return;
      }
      canvas.current.width = a.naturalWidth; canvas.current.height = a.naturalHeight;
      context.drawImage(a, 0, 0);
      const original = context.getImageData(0, 0, a.naturalWidth, a.naturalHeight);
      context.drawImage(b, 0, 0);
      const diff = context.getImageData(0, 0, a.naturalWidth, a.naturalHeight);
      let changed = 0;
      for (let p = 0; p < diff.data.length; p += 4) {
        const delta = Math.max(...[0, 1, 2, 3].map(c => Math.abs(diff.data[p + c] - original.data[p + c])));
        if (delta > 0) changed++;
        diff.data[p] = delta; diff.data[p + 1] = 0; diff.data[p + 2] = delta; diff.data[p + 3] = 255;
      }
      context.putImageData(diff, 0, 0);
      setStatus(`변경 픽셀 ${(100 * changed / (a.naturalWidth * a.naturalHeight)).toFixed(2)}% · 품질 판정은 검수 필요`);
      setReady(true);
    }).catch(() => { if (active) setStatus('이미지를 읽을 수 없습니다'); });
    return () => { active = false; };
  }, [baseline, candidate, name]);
  return <main className="frame-review" data-ready={ready}>
    <header><h1>프레임 비교</h1><a href="/">제작실</a></header>
    <div className="review-files">
      <label>기준 프레임<input aria-label="기준 프레임" type="file" multiple accept="image/*" onChange={e => load(e.target.files, setBaseline)} /></label>
      <label>후보 프레임<input aria-label="후보 프레임" type="file" multiple accept="image/*" onChange={e => load(e.target.files, setCandidate)} /></label>
    </div>
    <nav aria-label="프레임 탐색">
      <button aria-label="이전 프레임" disabled={index === 0} onClick={() => setIndex(index - 1)}>←</button>
      <select aria-label="현재 프레임" value={name ?? ''} onChange={e => setIndex(names.indexOf(e.target.value))}>{names.map(n => <option key={n}>{n}</option>)}</select>
      <button aria-label="다음 프레임" disabled={index >= names.length - 1} onClick={() => setIndex(index + 1)}>→</button>
    </nav>
    <p role="status">{status}</p>
    <div className="review-panels">
      <figure><figcaption>기준</figcaption>{baseline[name] && <img alt="기준" src={baseline[name]} />}</figure>
      <figure><figcaption>후보</figcaption>{candidate[name] && <img alt="후보" src={candidate[name]} />}</figure>
      <figure><figcaption>차이</figcaption><canvas aria-label="픽셀 차이" ref={canvas} /></figure>
    </div>
  </main>;
}
