import { buildStageTimeline, type RenderSegmentInput, type StageRunInput } from "./stage-timeline";

const duration = (value: number) => {
  const seconds = Math.round(value / 1000);
  const minutes = Math.floor(seconds / 60);
  return minutes ? `${minutes}분 ${seconds % 60}초` : `${seconds}초`;
};

const kind = (stage: string) => {
  if (stage.includes("image") || stage.includes("keycut") || stage.includes("asset")) return "image";
  if (stage.includes("voice") || stage.includes("audio")) return "voice";
  if (stage.includes("render") || stage.includes("video")) return "render";
  if (stage.includes("planning") || stage.includes("prompt") || stage.includes("harness")) return "planning";
  if (stage.includes("wait") || stage.includes("queue")) return "wait";
  return "other";
};

export function StageTimeline({ stages, renderSegments, stageLabel }: { stages: StageRunInput[]; renderSegments: RenderSegmentInput[]; stageLabel: (stage?: string) => string }) {
  const model = buildStageTimeline(stages, renderSegments);
  if (!model) return <p className="stage-timeline-empty">시작·종료 시각이 기록된 구간이 없습니다.</p>;
  return <div className="stage-timeline">
    <div className="stage-timeline-summary">
      <div><span>전체 경과시간</span><strong>{duration(model.elapsedMs)}</strong></div>
      <div><span>실제 작업이 있었던 시간</span><strong>{duration(model.activeDurationMs)}</strong></div>
      <div><span>모든 실제 작업시간 합계</span><strong>{duration(model.cumulativeDurationMs)}</strong></div>
      <div><span>병렬로 겹친 실제 작업</span><strong>{duration(model.overlapSavingsMs)}</strong></div>
      <div><span>최대 동시 작업</span><strong>{model.peakConcurrency}개</strong></div>
    </div>
    <p className="stage-timeline-help">막대는 실제 실행된 최하위 작업만 표시합니다. 입력을 기다린 선행 렌더 관리시간과 큐 대기는 제외했으며, 빈 구간은 실제 작업이 없었던 시간입니다.</p>
    <div className="stage-timeline-scroll">
      <div className="stage-timeline-canvas">
        <div className="stage-timeline-axis-label">구간</div>
        <div className="stage-timeline-axis">
          {model.ticks.map((tick) => <span key={tick.percent} style={{ left: `${tick.percent}%` }}>{duration(tick.offsetMs)}</span>)}
        </div>
        {model.groups.map((group) => <div className="stage-timeline-row" key={group.stage}>
            <div className="stage-timeline-label">
              <strong>{stageLabel(group.stage)}</strong>
              <span>실행 합계 {duration(group.cumulativeDurationMs)} · {group.runs.length}회{group.peakConcurrency > 1 ? ` · 최대 ${group.peakConcurrency}개 병렬` : ""}</span>
            </div>
            <div className="stage-timeline-track" style={{ height: `${Math.max(22, group.laneCount * 11 + 7)}px` }}>
              {model.ticks.map((tick) => <i className="stage-timeline-gridline" key={tick.percent} style={{ left: `${tick.percent}%` }} />)}
              {group.runs.map((run, index) => <span
                className={`stage-timeline-bar ${kind(group.stage)} ${run.status === "failed" ? "failed" : ""}`}
                key={`${run.startMs}-${index}`}
                style={{ left: `${run.offsetPercent}%`, width: `${Math.min(100 - run.offsetPercent, run.widthPercent)}%`, top: `${5 + run.lane * 11}px` }}
                title={`${stageLabel(group.stage)}${run.sceneId ? ` · ${run.sceneId}` : ""} · ${duration(run.durationMs)} · 시도 ${run.attempt}`}
              />)}
            </div>
          </div>)}
      </div>
    </div>
  </div>;
}

export function ActiveStageTable({ stages, renderSegments, stageLabel }: { stages: StageRunInput[]; renderSegments: RenderSegmentInput[]; stageLabel: (stage?: string) => string }) {
  const model = buildStageTimeline(stages, renderSegments);
  if (!model) return <p className="stage-timeline-empty">실제 실행시간 기록이 없습니다.</p>;
  return <div className="table-scroll"><table><thead><tr><th>구간</th><th>실행 수</th><th>실제 작업시간 합계</th><th>회당 평균</th><th>최대 동시 실행</th></tr></thead><tbody>
    {model.groups.map((group) => <tr key={group.stage}><td>{stageLabel(group.stage)}</td><td>{group.runs.length}회</td><td><strong>{duration(group.cumulativeDurationMs)}</strong></td><td>{duration(group.cumulativeDurationMs / group.runs.length)}</td><td>{group.peakConcurrency}개</td></tr>)}
  </tbody></table></div>;
}
