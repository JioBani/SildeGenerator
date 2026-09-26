const test = require('node:test');
const assert = require('node:assert/strict');
const { motionStyleSnapshot } = require('../dist/shared/motion-style');

test('motion styles select versioned production and image contracts', () => {
  const narrative = motionStyleSnapshot('narrative');
  const educational = motionStyleSnapshot('educational_info');
  assert.equal(narrative.version, '1.0.0');
  assert.equal(narrative.imagePreset, 'editorial_illustration');
  assert.equal(educational.imagePreset, 'graphic_explainer');
  assert.notDeepEqual(narrative.storyContract, educational.storyContract);
  narrative.storyContract.push('local change');
  assert.equal(motionStyleSnapshot('narrative').storyContract.includes('local change'), false);
});

test('local motion route is pinned only when enabled', () => {
  assert.equal(motionStyleSnapshot('narrative').productionRoute, undefined);
  assert.equal(motionStyleSnapshot('narrative', true).productionRoute, 'local_graphic');
  assert.equal(motionStyleSnapshot('educational_info').productionRoute, undefined);
});
