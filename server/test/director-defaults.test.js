const test = require('node:test');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const path = require('node:path');

test('fresh director defaults use terra low without inherited settings', () => {
  const env = Object.fromEntries(['PATH', 'SYSTEMROOT'].filter(k => process.env[k]).map(k => [k, process.env[k]]));
  const output = execFileSync(process.execPath, ['-e',
    `const {config}=require('./dist/config/app-config.js'); process.stdout.write(JSON.stringify([config.codexModel,config.codexReasoningEffort]));`],
    {cwd: path.resolve(__dirname, '..'), env, encoding: 'utf8'});
  assert.deepEqual(JSON.parse(output), ['gpt-5.6-terra', 'low']);
});
