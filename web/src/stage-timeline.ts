export type StageRunInput = Record<string, unknown>;

export type TimelineRun = {
  stage: string;
  sceneId: string | null;
  status: string;
  attempt: number;
  startMs: number;
  endMs: number;
  durationMs: number;
  offsetPercent: number;
  widthPercent: number;
  lane: number;
};

export type TimelineGroup = {
  stage: string;
  runs: TimelineRun[];
  laneCount: number;
  wallClockDurationMs: number;
  cumulativeDurationMs: number;
  peakConcurrency: number;
};

export type StageTimelineModel = {
  startMs: number;
  endMs: number;
  elapsedMs: number;
  cumulativeDurationMs: number;
  overlapSavingsMs: number;
  peakConcurrency: number;
  ticks: Array<{ percent: number; offsetMs: number }>;
  groups: TimelineGroup[];
};

const time = (value: unknown) => {
  if (typeof value !== "string" && !(value instanceof Date)) return Number.NaN;
  return new Date(value).getTime();
};

const peakConcurrency = (runs: Array<{ startMs: number; endMs: number }>) => {
  const events = runs.flatMap((run) => [
    { at: run.startMs, delta: 1 },
    { at: run.endMs, delta: -1 },
  ]).sort((a, b) => a.at - b.at || a.delta - b.delta);
  let active = 0;
  let peak = 0;
  for (const event of events) {
    active += event.delta;
    peak = Math.max(peak, active);
  }
  return peak;
};

export function buildStageTimeline(inputs: StageRunInput[]): StageTimelineModel | null {
  const parsed = inputs.flatMap((input) => {
    const startMs = time(input.started_at);
    let endMs = time(input.finished_at);
    const recordedDuration = Number(input.duration_ms);
    if (!Number.isFinite(endMs) && Number.isFinite(recordedDuration)) endMs = startMs + Math.max(0, recordedDuration);
    if (!Number.isFinite(startMs) || !Number.isFinite(endMs) || endMs < startMs) return [];
    return [{
      stage: String(input.stage ?? "unknown"),
      sceneId: input.scene_id === null || input.scene_id === undefined ? null : String(input.scene_id),
      status: String(input.status ?? "unknown"),
      attempt: Math.max(1, Number(input.attempt) || 1),
      startMs,
      endMs,
      durationMs: Math.max(0, Number.isFinite(recordedDuration) ? recordedDuration : endMs - startMs),
    }];
  });
  if (!parsed.length) return null;

  const startMs = Math.min(...parsed.map((run) => run.startMs));
  const endMs = Math.max(...parsed.map((run) => run.endMs));
  const elapsedMs = Math.max(1, endMs - startMs);
  const grouped = new Map<string, typeof parsed>();
  for (const run of parsed) grouped.set(run.stage, [...(grouped.get(run.stage) ?? []), run]);

  const groups = [...grouped.entries()].map(([stage, stageRuns]) => {
    const lanes: number[] = [];
    const runs = [...stageRuns].sort((a, b) => a.startMs - b.startMs || a.endMs - b.endMs).map((run) => {
      let lane = lanes.findIndex((lastEnd) => lastEnd <= run.startMs);
      if (lane < 0) { lane = lanes.length; lanes.push(run.endMs); } else lanes[lane] = run.endMs;
      return {
        ...run,
        offsetPercent: ((run.startMs - startMs) / elapsedMs) * 100,
        widthPercent: Math.max(((run.endMs - run.startMs) / elapsedMs) * 100, 0.35),
        lane,
      };
    });
    return {
      stage,
      runs,
      laneCount: Math.max(1, lanes.length),
      wallClockDurationMs: Math.max(...runs.map((run) => run.endMs)) - Math.min(...runs.map((run) => run.startMs)),
      cumulativeDurationMs: runs.reduce((sum, run) => sum + run.durationMs, 0),
      peakConcurrency: peakConcurrency(runs),
    };
  }).sort((a, b) => Math.min(...a.runs.map((run) => run.startMs)) - Math.min(...b.runs.map((run) => run.startMs)));

  const cumulativeDurationMs = parsed.reduce((sum, run) => sum + run.durationMs, 0);
  return {
    startMs,
    endMs,
    elapsedMs,
    cumulativeDurationMs,
    overlapSavingsMs: Math.max(0, cumulativeDurationMs - elapsedMs),
    peakConcurrency: peakConcurrency(parsed),
    ticks: [0, 25, 50, 75, 100].map((percent) => ({ percent, offsetMs: elapsedMs * percent / 100 })),
    groups,
  };
}
