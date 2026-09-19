import assert from "node:assert/strict";
import test from "node:test";
import { switchVoiceProvider } from "../.test-dist/voice-settings-draft.js";

test("provider round-trip restores the ElevenLabs voice instead of the Edge voice", () => {
  const eleven = { provider: "elevenlabs", model: "eleven_flash_v2_5", voiceId: "custom-eleven-voice", voiceName: "Custom", stability: 0.6, similarityBoost: 0.6, speed: 0.7 };
  const edge = switchVoiceProvider(eleven, "microsoft_edge", {}, eleven);
  assert.equal(edge.draft.voiceId, "ko-KR-InJoonNeural");
  const restored = switchVoiceProvider(edge.draft, "elevenlabs", edge.memory, eleven);
  assert.equal(restored.draft.voiceId, "custom-eleven-voice");
  assert.equal(restored.draft.model, "eleven_flash_v2_5");
});

test("unsaved provider edits survive a temporary provider switch", () => {
  const eleven = { provider: "elevenlabs", model: "eleven_multilingual_v2", voiceId: "edited-before-switch", voiceName: "Edited", stability: 0.75, similarityBoost: 0.65, speed: 0.85 };
  const edge = switchVoiceProvider(eleven, "microsoft_edge", {}, null);
  const restored = switchVoiceProvider(edge.draft, "elevenlabs", edge.memory, null);
  assert.equal(restored.draft.voiceId, "edited-before-switch");
  assert.equal(restored.draft.speed, 0.85);
});
