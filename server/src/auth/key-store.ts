import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
export type KeyRecord = { userId: string; label: string; createdAt: string; revokedAt?: string };
export const keyFile = process.env.KEY_FILE || '/keys/keys.json';
export const hashKey = (key: string) => createHash('sha256').update(key).digest('hex');
export function readKeys(): Record<string, KeyRecord> { return JSON.parse(readFileSync(keyFile, 'utf8')); }
