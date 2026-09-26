const test = require('node:test');
const assert = require('node:assert/strict');
require('reflect-metadata');
const { VIDEO_GENRES, GENRE_VERSION } = require('../dist/shared/video-genre');
const { GENRE_OPTIONS, supportsGenreDraft, defaultImageStyleForGenre } = require('../dist/shared/video-genre');

test('one public motion-graphics format replaces superficial genre choices', () => {
  assert.deepEqual(VIDEO_GENRES, ['motion_graphic']);
  assert.equal(GENRE_VERSION, '1.0.0');
  assert.equal(supportsGenreDraft('motion_graphic', 'classic-slide'), false);
  assert.equal(supportsGenreDraft('motion_graphic', 'genre-slide'), false);
  assert.equal(supportsGenreDraft('motion_graphic', 'astra-motion'), true);
  assert.equal(GENRE_OPTIONS[0].humanReviewRequired, true);
  assert.equal(GENRE_OPTIONS[0].productionAvailable, true);
  assert.equal(GENRE_OPTIONS[0].status, 'internal_contract');
  assert.deepEqual(GENRE_OPTIONS[0].supportedHarnesses, ['astra-motion']);
});

test('surface art style is independent from the production format', () => {
  assert.equal(GENRE_OPTIONS[0].defaultImageStyle, 'graphic_explainer');
  assert.equal(defaultImageStyleForGenre('motion_graphic'), 'graphic_explainer');
});
