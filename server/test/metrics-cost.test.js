const assert = require("node:assert/strict");
const test = require("node:test");
const { estimateUsageCost } = require("../dist/metrics/metrics.service");

test("GPT Image 2.5 API estimate separates text, reference image, and output image tokens", () => {
  const result = estimateUsageCost({
    provider: "chatgpt_oauth_image",
    model: "gpt-image-2.5-sunburst",
    stage: "image_generation",
    input_tokens: 2100,
    cached_input_tokens: 0,
    output_tokens: 500,
    started_at: new Date(0).toISOString(),
    raw_usage: {
      image: { input_tokens_details: { text_tokens: 100, image_tokens: 2000 } },
    },
  });

  assert.equal(result.actual, null);
  assert.equal(result.equivalent, 0.0315);
  assert.deepEqual(result.snapshot.tokenBreakdown, {
    textInput: 100,
    imageInput: 2000,
    cachedText: 0,
    cachedImage: 0,
    outputImage: 500,
  });
});
