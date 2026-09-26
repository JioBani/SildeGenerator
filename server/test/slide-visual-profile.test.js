const test = require('node:test');
const assert = require('node:assert/strict');
const { slideVisualProfile } = require('../dist/shared/slide-visual-profile');

test('slide illustration profile is versioned and style scoped', () => {
  assert.deepEqual(slideVisualProfile('cute_character'), {
    id: 'local_illustration', version: '0.5.0', imageStyle: 'cute_character',
  });
  assert.throws(() => slideVisualProfile('graphic_explainer'));
});
