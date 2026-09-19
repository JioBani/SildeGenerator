const assert = require("node:assert/strict");
const test = require("node:test");
const { DEFAULT_IMAGE_MODEL, IMAGE_MODELS } = require("../dist/shared/image-model");

test("exposes exactly the three selectable image models", () => {
  assert.deepEqual(IMAGE_MODELS, [
    "gpt-image-2",
    "gpt-image-2.5-sunburst",
    "gpt-image-2.5-flare",
  ]);
  assert.equal(DEFAULT_IMAGE_MODEL, "gpt-image-2.5-sunburst");
});
