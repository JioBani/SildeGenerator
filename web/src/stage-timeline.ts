export type StageRunInput = Record<string, unknown>;
export type RenderSegmentInput = Record<string, unknown>;

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
  activeDurationMs: number;
  idleDurationMs: number;
  scaleDurationMs: number;
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

const unionDuration = (runs: Array<{ startMs: number; endMs: number }>) => {
  const ordered = [...runs].sort((a, b) => a.startMs - b.startMs || a.endMs - b.endMs);
  let total = 0;
  let start = Number.NaN;
  let end = Number.NaN;
  for (const run of ordered) {
    if (!Number.isFinite(start)) { start = run.startMs; end = run.endMs; continue; }
    if (run.startMs > end) { total += end - start; start = run.startMs; end = run.endMs; }
    else end = Math.max(end, run.endMs);
  }
  return Number.isFinite(start) ? total + end - start : 0;
};

const COORDINATOR_STAGES = new Set(["progressive_video_render", "asset_generation", "queue_wait", "retry_wait"]);
const NICE_TICK_INTERVALS_MS = [5_000, 10_000, 15_000, 30_000, 60_000, 120_000, 300_000, 600_000, 900_000, 1_800_000, 3_600_000];

const timelineScale = (elapsedMs: number) => {
  const intervalMs = NICE_TICK_INTERVALS_MS.find((candidate) => Math.ceil(elapsedMs / candidate) <= 6)
    ?? NICE_TICK_INTERVALS_MS[NICE_TICK_INTERVALS_MS.length - 1];
  const scaleDurationMs = Math.max(intervalMs, Math.ceil(elapsedMs / intervalMs) * intervalMs);
  const count = Math.round(scaleDurationMs / intervalMs);
  return {
    scaleDurationMs,
    ticks: Array.from({ length: count + 1 }, (_, index) => ({
      percent: index / count * 100,
      offsetMs: index * intervalMs,
    })),
  };
};

export function buildStageTimeline(inputs: StageRunInput[], renderSegments: RenderSegmentInput[] = []): StageTimelineModel | null {
  const actualInputs = [
    ...inputs.filter((input) => !COORDINATOR_STAGES.has(String(input.stage ?? ""))),
    ...renderSegments.flatMap((segment) => {
      if (!segment.started_at || !segment.finished_at) return [];
      return [{
        stage: "segment_render",
        scene_id: `${String(segment.first_scene_id ?? "-")}–${String(segment.last_scene_id ?? "-")}`,
        status: segment.status ?? "unknown",
        attempt: 1,
        started_at: segment.started_at,
        finished_at: segment.finished_at,
        duration_ms: segment.duration_ms,
      }];
    }),
  ];
  const parsed = actualInputs.flatMap((input) => {
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
  const scale = timelineScale(elapsedMs);
  const grouped = new Map<string, typeof parsed>();
  for (const run of parsed) grouped.set(run.stage, [...(grouped.get(run.stage) ?? []), run]);

  const groups = [...grouped.entries()].map(([stage, stageRuns]) => {
    const lanes: number[] = [];
    const runs = [...stageRuns].sort((a, b) => a.startMs - b.startMs || a.endMs - b.endMs).map((run) => {
      let lane = lanes.findIndex((lastEnd) => lastEnd <= run.startMs);
      if (lane < 0) { lane = lanes.length; lanes.push(run.endMs); } else lanes[lane] = run.endMs;
      return {
        ...run,
        offsetPercent: ((run.startMs - startMs) / scale.scaleDurationMs) * 100,
        widthPercent: Math.max(((run.endMs - run.startMs) / scale.scaleDurationMs) * 100, 0.35),
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
  const activeDurationMs = unionDuration(parsed);
  return {
    startMs,
    endMs,
    elapsedMs,
    activeDurationMs,
    idleDurationMs: Math.max(0, elapsedMs - activeDurationMs),
    scaleDurationMs: scale.scaleDurationMs,
    cumulativeDurationMs,
    overlapSavingsMs: Math.max(0, cumulativeDurationMs - activeDurationMs),
    peakConcurrency: peakConcurrency(parsed),
    ticks: scale.ticks,
    groups,
  };
}
