import { randomBytes } from 'node:crypto';
import { closeSync, mkdirSync, openSync, renameSync, unlinkSync, writeFileSync } from 'node:fs';
import { dirname } from 'node:path';
import { hashKey, keyFile, readKeys } from './key-store';
const [command, userId, value, explicitLabel] = process.argv.slice(2);
if (!['issue', 'set', 'revoke', 'list'].includes(command) || (command !== 'list' && !/^[a-zA-Z0-9_-]{1,64}$/.test(userId || ''))) {
  throw new Error('Usage: keyctl issue USER [LABEL] | set USER TOKEN [LABEL] | revoke USER | list');
}
if (command === 'set' && !/^\S{6,256}$/.test(value || '')) throw new Error('TOKEN must be 6-256 non-whitespace characters');
mkdirSync(dirname(keyFile), { recursive: true, mode: 0o700 });
const lock = `${keyFile}.lock`;
const fd = openSync(lock, 'wx', 0o600);
try {
  let keys: ReturnType<typeof readKeys> = {};
  try { keys = readKeys(); } catch (e: any) { if (e.code !== 'ENOENT') throw e; }
  if (command === 'list') console.log(JSON.stringify(Object.values(keys), null, 2));
  else {
    let token: string | undefined;
    if (command === 'issue') {
      token = `sg_${randomBytes(32).toString('base64url')}`;
      keys[hashKey(token)] = { userId, label: value || 'default', createdAt: new Date().toISOString() };
    } else if (command === 'set') {
      for (const key of Object.values(keys)) if (key.userId === userId && !key.revokedAt) key.revokedAt = new Date().toISOString();
      token = value;
      keys[hashKey(token)] = { userId, label: explicitLabel || 'fixed', createdAt: new Date().toISOString() };
    } else for (const key of Object.values(keys)) if (key.userId === userId) key.revokedAt = new Date().toISOString();
    const tmp = `${keyFile}.${process.pid}.tmp`;
    writeFileSync(tmp, JSON.stringify(keys, null, 2), { mode: 0o600 });
    renameSync(tmp, keyFile);
    if (command === 'set') console.log(`Set fixed token for ${userId}`);
    else console.log(token || `Revoked all keys for ${userId}`);
  }
} finally { closeSync(fd); unlinkSync(lock); }
