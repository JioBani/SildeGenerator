const assert = require("node:assert/strict");
const test = require("node:test");
const { DEFAULT_IMAGE_STYLE, IMAGE_STYLES } = require("../dist/shared/image-style");

test("exposes the three fixed image styles with editorial default", () => {
  assert.deepEqual(IMAGE_STYLES, [
    "editorial_illustration",
    "cinematic_realism",
    "graphic_explainer",
  ]);
  assert.equal(DEFAULT_IMAGE_STYLE, "editorial_illustration");
});
