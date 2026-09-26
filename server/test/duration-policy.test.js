const test = require('node:test');
const assert = require('node:assert/strict');
const { durationProfileForHarness, estimatedNarrationSeconds, maximumSeconds } = require('../dist/shared/duration-policy');

test('slide video uses a single 30-minute contract while motion keeps its episode contract', () => {
  assert.equal(durationProfileForHarness('classic-slide'), 'single_30m');
  assert.equal(durationProfileForHarness('cinematic-slide'), 'single_30m');
  assert.equal(durationProfileForHarness('astra-motion'), 'episode_60');
  assert.equal(maximumSeconds('single_30m'), 1800);
  assert.equal(maximumSeconds('episode_60'), 60);
});

test('server estimate follows the same speed relationship as the creator', () => {
  assert.equal(estimatedNarrationSeconds('한국어 대본', 0.7), '한국어 대본'.length / 5.7);
  assert.ok(Math.abs(estimatedNarrationSeconds('한국어 대본', 1.2) - estimatedNarrationSeconds('한국어 대본', 0.7) * 0.7 / 1.2) < 1e-12);
});

test('Edge Korean voice uses a conservative measured duration for a 60-second motion job', () => {
  assert.ok(estimatedNarrationSeconds('가'.repeat(514), 1.1, 'microsoft_edge') > 60);
  assert.ok(estimatedNarrationSeconds('가'.repeat(120), 1.1, 'microsoft_edge') < 60);
});
