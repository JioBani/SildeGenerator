const assert = require("node:assert/strict");
const test = require("node:test");
const { isDownloadableVideo } = require("../dist/jobs/safe-video");

test("completed videos are downloadable regardless of their streamed file size", () => {
  assert.equal(isDownloadableVideo({ isFile: () => true, size: 36_067_008 }), true);
  assert.equal(isDownloadableVideo({ isFile: () => true, size: 1024 * 1024 * 1024 }), true);
});

test("empty or non-file artifacts are rejected", () => {
  assert.equal(isDownloadableVideo({ isFile: () => true, size: 0 }), false);
  assert.equal(isDownloadableVideo({ isFile: () => false, size: 36_067_008 }), false);
});
