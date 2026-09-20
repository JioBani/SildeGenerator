import assert from "node:assert/strict";
import test from "node:test";
import { buildCostBreakdown } from "../.test-dist/cost-breakdown.js";

test("cost breakdown reports amount and percentage for each provider class", () => {
  const model = buildCostBreakdown({ inferenceCostKrw: 20, imageCostKrw: 70, voiceCostKrw: 10 });
  assert.equal(model.total, 100);
  assert.deepEqual(model.slices.map((slice) => slice.percent), [20, 70, 10]);
  assert.match(model.gradient, /^conic-gradient/);
});
