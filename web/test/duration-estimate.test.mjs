import assert from "node:assert/strict";
import test from "node:test";
import { estimateNarrationDuration } from "../.test-dist/duration-estimate.js";

test("empty input has no estimate and whitespace is normalized", () => {
  assert.equal(estimateNarrationDuration(" \n\t "), null);
  assert.equal(estimateNarrationDuration("가  \n 나").normalizedCharacters, 3);
});

test("measured Korean narration rate maps representative lengths", () => {
  assert.equal(estimateNarrationDuration("가".repeat(57)).centerSeconds, 10);
  assert.equal(estimateNarrationDuration("가".repeat(342)).centerSeconds, 60);
  assert.equal(estimateNarrationDuration("가".repeat(1710)).centerSeconds, 300);
});

test("displayed center and range use five-second rounding except the one-second minimum", () => {
  assert.equal(estimateNarrationDuration("가").centerSeconds, 1);
  assert.equal(estimateNarrationDuration("가".repeat(20)).centerSeconds, 5);
  assert.equal(estimateNarrationDuration("가".repeat(100)).centerSeconds, 20);
  assert.equal(estimateNarrationDuration("가".repeat(500)).centerSeconds, 90);
  const estimate = estimateNarrationDuration("가".repeat(200));
  assert.equal(estimate.centerSeconds % 5, 0);
  assert.equal(estimate.minSeconds % 5, 0);
  assert.equal(estimate.maxSeconds % 5, 0);
});

test("narration speed changes the estimated playback duration", () => {
  const script = "가".repeat(342);
  assert.equal(estimateNarrationDuration(script, .75).centerSeconds, 80);
  assert.equal(estimateNarrationDuration(script, 1).centerSeconds, 60);
  assert.equal(estimateNarrationDuration(script, 1.5).centerSeconds, 40);
});
