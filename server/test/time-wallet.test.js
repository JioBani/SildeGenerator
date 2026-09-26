const test = require('node:test');
const assert = require('node:assert/strict');
const { chargeForActual, reserveTime, settleTime, releaseTime } = require('../dist/wallet/time-wallet');

test('settlement never spends time reserved for another job', () => {
  assert.equal(chargeForActual(120, 100, 50, 100), 70);
  assert.equal(chargeForActual(120, 100, 50, 20.1), 21);
  assert.equal(chargeForActual(120, 100, 50, 500), 70);
  assert.equal(chargeForActual(50, 50, 50, 999), 50);
});

test('reservation rejects insufficient available time', async () => {
  const client = { query: async (sql) => {
    if (sql.includes('SELECT balance_seconds')) return { rows: [{ balance_seconds: '60', reserved_seconds: '30' }] };
    return { rows: [] };
  } };
  await assert.rejects(() => reserveTime(client, 'user', 'job', 40), { status: 400 });
});

test('settlement is idempotent and failure releases only an active reservation', async () => {
  const statements = [];
  const client = { query: async (sql) => {
    statements.push(sql);
    if (sql.includes('SELECT user_id,reserved_seconds,status,charged_seconds')) return {
      rows: [{ user_id: 'user', reserved_seconds: '50', status: 'settled', charged_seconds: '42' }],
    };
    if (sql.includes('SELECT user_id,reserved_seconds,status')) return {
      rows: [{ user_id: 'user', reserved_seconds: '50', status: 'released' }],
    };
    return { rows: [] };
  } };
  assert.equal(await settleTime(client, 'job', 60), 42);
  await releaseTime(client, 'job');
  assert.equal(statements.filter((sql) => sql.startsWith('UPDATE')).length, 0);
});
