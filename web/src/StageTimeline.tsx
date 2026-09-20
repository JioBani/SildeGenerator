import { buildStageTimeline, type StageRunInput } from "./stage-timeline";

type StageSummary = { stage: string; runs: number; wallClockDurationMs: number | string; totalDurationMs: number | string; averageDurationMs: number | string };

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

export function StageTimeline({ stages, summaries, stageLabel }: { stages: StageRunInput[]; summaries: StageSummary[]; stageLabel: (stage?: string) => string }) {
  const model = buildStageTimeline(stages);
  if (!model) return <p className="stage-timeline-empty">시작·종료 시각이 기록된 구간이 없습니다.</p>;
  const summaryByStage = new Map(summaries.map((summary) => [summary.stage, summary]));
  return <div className="stage-timeline">
    <div className="stage-timeline-summary">
      <div><span>실제 전체 경과</span><strong>{duration(model.elapsedMs)}</strong></div>
      <div><span>작업시간 단순 합계</span><strong>{duration(model.cumulativeDurationMs)}</strong></div>
      <div><span>병렬 실행으로 겹친 시간</span><strong>{duration(model.overlapSavingsMs)}</strong></div>
      <div><span>최대 동시 작업</span><strong>{model.peakConcurrency}개</strong></div>
    </div>
    <p className="stage-timeline-help">가로축은 실제 시각입니다. 같은 세로선에 놓인 막대는 동시에 실행된 작업이며, 한 행의 여러 층은 해당 구간의 병렬 슬롯을 뜻합니다.</p>
    <div className="stage-timeline-scroll">
      <div className="stage-timeline-canvas">
        <div className="stage-timeline-axis-label">구간</div>
        <div className="stage-timeline-axis">
          {model.ticks.map((tick) => <span key={tick.percent} style={{ left: `${tick.percent}%` }}>{duration(tick.offsetMs)}</span>)}
        </div>
        {model.groups.map((group) => {
          const summary = summaryByStage.get(group.stage);
          const wall = Number(summary?.wallClockDurationMs ?? group.wallClockDurationMs);
          const cumulative = Number(summary?.totalDurationMs ?? group.cumulativeDurationMs);
          return <div className="stage-timeline-row" key={group.stage}>
            <div className="stage-timeline-label">
              <strong>{stageLabel(group.stage)}</strong>
              <span>실제 {duration(wall)} · 합계 {duration(cumulative)}{group.peakConcurrency > 1 ? ` · 최대 ${group.peakConcurrency}개 병렬` : ""}</span>
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
          </div>;
        })}
      </div>
    </div>
  </div>;
}
