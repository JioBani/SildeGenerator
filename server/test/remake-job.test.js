const test = require('node:test');
const assert = require('node:assert/strict');
const { JobsService } = require('../dist/jobs/jobs.service');

test('remake reads only the owner job and forwards the saved settings', async () => {
  const service = Object.create(JobsService.prototype);
  let requested;
  service.db = { query: async (sql, values) => {
    requested = values;
    return { rows: [{
      id: values[0], scenario_input: '[시나리오] 원래 제목\n본문입니다.', scenario: '본문입니다.',
      image_model: 'gpt-image-2', continuity_enabled: true, image_style: 'cute_character',
      harness_id: 'classic-slide', harness_snapshot: { id: 'classic-slide', source_sha256: 'abc' },
      narration_speed: '0.85', aspect_ratio: '9:16', subtitles_enabled: false,
      voice_settings: { provider: 'elevenlabs', model: 'voice-model', voiceId: 'speaker-1', version: 2 },
      codex_model: 'gpt-5.6-terra', codex_effort: 'low', codex_fast_mode: false,
    }] };
  } };
  let argumentsSeen;
  service.create = async (...args) => { argumentsSeen = args; return { id: 'new-job' }; };
  const result = await service.remake('original', 'owner');
  assert.equal(result.id, 'new-job');
  assert.deepEqual(requested, ['original', 'owner']);
  assert.equal(argumentsSeen[0], '[시나리오] 원래 제목\n본문입니다.');
  assert.equal(argumentsSeen[7], '9:16');
  assert.equal(argumentsSeen[8], false);
  assert.equal(argumentsSeen[9].voice.voiceId, 'speaker-1');
});

test('remake refuses jobs absent from the owner query', async () => {
  const service = Object.create(JobsService.prototype);
  service.db = { query: async () => ({ rows: [] }) };
  await assert.rejects(() => service.remake('someone-elses-job', 'owner'), { status: 404 });
});
