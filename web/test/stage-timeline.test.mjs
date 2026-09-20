import assert from "node:assert/strict";
import test from "node:test";
import { buildStageTimeline } from "../.test-dist/stage-timeline.js";

const at = (seconds) => new Date(Date.UTC(2026, 0, 1, 0, 0, seconds)).toISOString();

test("timeline exposes wall-clock placement and parallel work separately", () => {
  const model = buildStageTimeline([
    { stage: "scene_planning", started_at: at(0), finished_at: at(10), duration_ms: 10_000, status: "succeeded" },
    { stage: "image_generation", scene_id: "scene-001", started_at: at(10), finished_at: at(40), duration_ms: 30_000, status: "succeeded" },
    { stage: "image_generation", scene_id: "scene-002", started_at: at(10), finished_at: at(35), duration_ms: 25_000, status: "succeeded" },
    { stage: "voice_generation", scene_id: "scene-001", started_at: at(12), finished_at: at(20), duration_ms: 8_000, status: "succeeded" },
  ]);
  assert.ok(model);
  assert.equal(model.elapsedMs, 40_000);
  assert.equal(model.cumulativeDurationMs, 73_000);
  assert.equal(model.overlapSavingsMs, 33_000);
  assert.equal(model.peakConcurrency, 3);
  const images = model.groups.find((group) => group.stage === "image_generation");
  assert.equal(images.laneCount, 2);
  assert.equal(images.peakConcurrency, 2);
  assert.equal(images.wallClockDurationMs, 30_000);
  assert.equal(images.cumulativeDurationMs, 55_000);
  assert.deepEqual(images.runs.map((run) => run.lane), [0, 1]);
});

test("timeline reuses a lane for sequential work and falls back to recorded duration", () => {
  const model = buildStageTimeline([
    { stage: "image_generation", started_at: at(0), finished_at: at(5), duration_ms: 5_000 },
    { stage: "image_generation", started_at: at(5), duration_ms: 7_000 },
  ]);
  assert.ok(model);
  assert.equal(model.elapsedMs, 12_000);
  assert.equal(model.groups[0].laneCount, 1);
  assert.deepEqual(model.groups[0].runs.map((run) => run.lane), [0, 0]);
});
