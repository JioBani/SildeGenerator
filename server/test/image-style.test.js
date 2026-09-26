const assert = require("node:assert/strict");
const test = require("node:test");
const { DEFAULT_IMAGE_STYLE, IMAGE_STYLES } = require("../dist/shared/image-style");

test("exposes cinematic styles without changing the legacy default", () => {
  assert.deepEqual(IMAGE_STYLES, [
    "editorial_illustration",
    "cinematic_realism",
    "graphic_explainer",
    "cute_character",
    "fantasy_anime",
    "animation_3d",
    "disney_animation",
    "dystopian",
  ]);
  assert.equal(DEFAULT_IMAGE_STYLE, "editorial_illustration");
});
