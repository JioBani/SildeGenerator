const test = require('node:test');
const assert = require('node:assert/strict');
const { assertRunnerConfiguration } = require('../dist/worker/runners/http.runner');

test('runner preflight rejects a live site backed by a mock runner', () => {
  const expected = { mode: 'live', imageProvider: 'oauth' };
  assert.throws(() => assertRunnerConfiguration({ mode: 'mock', imageProvider: 'mock' }, expected), /설정 불일치/);
  assert.doesNotThrow(() => assertRunnerConfiguration({ mode: 'live', imageProvider: 'oauth' }, expected));
});
