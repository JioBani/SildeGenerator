const test = require('node:test');
const assert = require('node:assert/strict');
const { audioFormat } = require('../dist/jobs/music-upload');
const { autoMusicPreset, publicMusicSelection } = require('../dist/shared/music-selection');

test('uploaded music must have a supported audio signature', () => {
  assert.deepEqual(audioFormat(Buffer.from('RIFFxxxxWAVEyyyy')), { mimeType: 'audio/wav', extension: '.wav' });
  assert.deepEqual(audioFormat(Buffer.from('ID3xxxxxxxxx')), { mimeType: 'audio/mpeg', extension: '.mp3' });
  assert.throws(() => audioFormat(Buffer.from('not audio at all')));
});

test('automatic music preset follows the narration and style', () => {
  assert.equal(autoMusicPreset('슬픔이 남았습니다', 'cute_character'), 'quiet-reflection');
  assert.equal(autoMusicPreset('용이 날아갑니다', 'fantasy_anime'), 'fantasy-night');
  assert.equal(autoMusicPreset('숲을 걷습니다', 'cute_character'), 'warm-story');
});

test('public job status does not reveal the managed music path or digest', () => {
  assert.deepEqual(publicMusicSelection({ mode: 'upload', uploadId: 'track', path: '/data/private.wav', sha256: 'abc', mimeType: 'audio/wav' }),
    { mode: 'upload', uploadId: 'track' });
});
