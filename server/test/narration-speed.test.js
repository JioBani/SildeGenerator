const assert = require("node:assert/strict");
const test = require("node:test");

const {
  applyNarrationSpeed,
  DEFAULT_NARRATION_SPEED,
  MAX_NARRATION_SPEED,
  MIN_NARRATION_SPEED,
} = require("../dist/shared/voice-settings.js");

const base = {
  model: "voice-model",
  voiceId: "voice-id",
  voiceName: "Voice",
  version: 1,
};

test("ElevenLabs narration speed is written to the native provider setting", () => {
  const result = applyNarrationSpeed({ ...base, provider: "elevenlabs", speed: 0.7 }, 1.15);
  assert.equal(result.speed, 1.15);
  assert.equal("playbackSpeed" in result, false);
});

test("Microsoft Edge narration speed is converted to its native signed rate", () => {
  assert.equal(applyNarrationSpeed({ ...base, provider: "microsoft_edge", rate: "-30%" }, 0.7).rate, "-30%");
  assert.equal(applyNarrationSpeed({ ...base, provider: "microsoft_edge", rate: "-30%" }, 1).rate, "+0%");
  assert.equal(applyNarrationSpeed({ ...base, provider: "microsoft_edge", rate: "-30%" }, 1.2).rate, "+20%");
});

test("shared narration speed range matches provider-native limits", () => {
  assert.equal(DEFAULT_NARRATION_SPEED, 0.7);
  assert.equal(MIN_NARRATION_SPEED, 0.7);
  assert.equal(MAX_NARRATION_SPEED, 1.2);
});
