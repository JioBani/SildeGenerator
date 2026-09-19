const assert = require("node:assert/strict");
const test = require("node:test");
const { config } = require("../dist/config/app-config");

test("safe first-phase pipeline defaults are 24fps and two voice slots", () => {
  assert.equal(config.videoFps, 24);
  assert.equal(config.voiceConcurrency, 2);
  assert.equal(config.videoJobGlobalConcurrency, 1);
  assert.equal(config.concurrency, 1);
  assert.equal(config.userPending, 20);
  assert.equal(config.globalPending, 20);
  assert.equal(config.dailyJobs, 0);
});
