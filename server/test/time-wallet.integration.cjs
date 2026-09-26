const test = require('node:test');
const assert = require('node:assert/strict');
const { Pool } = require('pg');
const { randomUUID } = require('node:crypto');
const { grantVerifiedTime, reserveTime, settleTime, releaseTime } = require('../dist/wallet/time-wallet');

test('PostgreSQL wallet reserves concurrent work and settles only actual seconds', {
  skip: !process.env.WALLET_TEST_DATABASE_URL,
}, async () => {
  const pool = new Pool({ connectionString: process.env.WALLET_TEST_DATABASE_URL });
  const client = await pool.connect();
  const job1 = randomUUID();
  const job2 = randomUUID();
  try {
    await client.query(`CREATE TEMP TABLE generation_jobs(id uuid PRIMARY KEY)`);
    await client.query(`CREATE TEMP TABLE time_wallets(user_id text PRIMARY KEY,balance_seconds bigint NOT NULL DEFAULT 0 CHECK(balance_seconds>=0),reserved_seconds bigint NOT NULL DEFAULT 0 CHECK(reserved_seconds>=0 AND reserved_seconds<=balance_seconds),updated_at timestamptz DEFAULT now())`);
    await client.query(`CREATE TEMP TABLE time_reservations(job_id uuid PRIMARY KEY REFERENCES generation_jobs(id),user_id text NOT NULL REFERENCES time_wallets(user_id),reserved_seconds bigint NOT NULL,charged_seconds bigint NOT NULL DEFAULT 0,status text NOT NULL,created_at timestamptz DEFAULT now(),finished_at timestamptz)`);
    await client.query(`CREATE TEMP TABLE time_wallet_entries(id bigserial PRIMARY KEY,user_id text NOT NULL,job_id uuid,kind text NOT NULL,seconds bigint NOT NULL,external_reference text UNIQUE,UNIQUE(job_id,kind))`);
    await client.query(`INSERT INTO generation_jobs(id) VALUES($1),($2)`, [job1, job2]);
    await grantVerifiedTime(client, 'test-user', 120, 'mock-payment-1');
    await grantVerifiedTime(client, 'test-user', 120, 'mock-payment-1');
    await reserveTime(client, 'test-user', job1, 50);
    await reserveTime(client, 'test-user', job2, 50);
    await assert.rejects(() => reserveTime(client, 'test-user', randomUUID(), 30), { status: 400 });
    assert.equal(await settleTime(client, job1, 100), 70);
    assert.equal(await settleTime(client, job1, 100), 70);
    await releaseTime(client, job2);
    await releaseTime(client, job2);
    const state = await client.query(`SELECT balance_seconds,reserved_seconds FROM time_wallets WHERE user_id='test-user'`);
    assert.equal(Number(state.rows[0].balance_seconds), 50);
    assert.equal(Number(state.rows[0].reserved_seconds), 0);
    const ledger = await client.query(`SELECT kind,seconds FROM time_wallet_entries ORDER BY id`);
    assert.deepEqual(ledger.rows.map((row) => [row.kind, Number(row.seconds)]), [['grant', 120], ['settle', -70]]);
  } finally {
    client.release();
    await pool.end();
  }
});
