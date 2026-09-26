import { BadRequestException } from "@nestjs/common";
import type { PoolClient } from "pg";

export function chargeForActual(balance: number, allReserved: number, thisReserved: number, actual: number): number {
  return Math.max(0, Math.min(Math.ceil(actual), balance - (allReserved - thisReserved)));
}

export async function reserveTime(client: PoolClient, userId: string, jobId: string, estimatedSeconds: number): Promise<void> {
  const seconds = Math.max(1, Math.ceil(estimatedSeconds));
  await client.query(`INSERT INTO time_wallets(user_id) VALUES($1) ON CONFLICT(user_id) DO NOTHING`, [userId]);
  const current = await client.query<{ balance_seconds: string; reserved_seconds: string }>(
    `SELECT balance_seconds,reserved_seconds FROM time_wallets WHERE user_id=$1 FOR UPDATE`, [userId]);
  const balance = Number(current.rows[0].balance_seconds);
  const reserved = Number(current.rows[0].reserved_seconds);
  if (balance - reserved < seconds) throw new BadRequestException("영상 제작 가능 시간이 부족합니다.");
  await client.query(`UPDATE time_wallets SET reserved_seconds=reserved_seconds+$2,updated_at=now() WHERE user_id=$1`, [userId, seconds]);
  await client.query(`INSERT INTO time_reservations(job_id,user_id,reserved_seconds,status) VALUES($1,$2,$3,'reserved')`, [jobId, userId, seconds]);
}

export async function settleTime(client: PoolClient, jobId: string, actualSeconds: number): Promise<number> {
  const reservation = await client.query<{ user_id: string; reserved_seconds: string; status: string; charged_seconds: string }>(
    `SELECT user_id,reserved_seconds,status,charged_seconds FROM time_reservations WHERE job_id=$1 FOR UPDATE`, [jobId]);
  const row = reservation.rows[0];
  if (!row) throw new Error("time reservation missing for completed job");
  if (row.status === "settled") return Number(row.charged_seconds);
  if (row.status !== "reserved") throw new Error("released reservation cannot be settled");
  if (!Number.isFinite(actualSeconds) || actualSeconds <= 0) throw new Error("actual video duration is unavailable");
  const wallet = await client.query<{ balance_seconds: string; reserved_seconds: string }>(
    `SELECT balance_seconds,reserved_seconds FROM time_wallets WHERE user_id=$1 FOR UPDATE`, [row.user_id]);
  const held = Number(row.reserved_seconds);
  const charged = chargeForActual(Number(wallet.rows[0].balance_seconds), Number(wallet.rows[0].reserved_seconds), held, actualSeconds);
  await client.query(`UPDATE time_wallets SET balance_seconds=balance_seconds-$2,reserved_seconds=reserved_seconds-$3,updated_at=now() WHERE user_id=$1`, [row.user_id, charged, held]);
  await client.query(`UPDATE time_reservations SET status='settled',charged_seconds=$2,finished_at=now() WHERE job_id=$1`, [jobId, charged]);
  await client.query(`INSERT INTO time_wallet_entries(user_id,job_id,kind,seconds) VALUES($1,$2,'settle',$3) ON CONFLICT(job_id,kind) DO NOTHING`, [row.user_id, jobId, -charged]);
  return charged;
}

export async function releaseTime(client: PoolClient, jobId: string): Promise<void> {
  const reservation = await client.query<{ user_id: string; reserved_seconds: string; status: string }>(
    `SELECT user_id,reserved_seconds,status FROM time_reservations WHERE job_id=$1 FOR UPDATE`, [jobId]);
  const row = reservation.rows[0];
  if (!row || row.status !== "reserved") return;
  await client.query(`UPDATE time_wallets SET reserved_seconds=reserved_seconds-$2,updated_at=now() WHERE user_id=$1`, [row.user_id, Number(row.reserved_seconds)]);
  await client.query(`UPDATE time_reservations SET status='released',finished_at=now() WHERE job_id=$1`, [jobId]);
}

export async function grantVerifiedTime(client: PoolClient, userId: string, seconds: number, externalReference: string): Promise<void> {
  if (!Number.isSafeInteger(seconds) || seconds <= 0 || !externalReference) throw new Error("invalid grant");
  await client.query(`INSERT INTO time_wallets(user_id) VALUES($1) ON CONFLICT(user_id) DO NOTHING`, [userId]);
  const result = await client.query(`INSERT INTO time_wallet_entries(user_id,kind,seconds,external_reference)
    VALUES($1,'grant',$2,$3) ON CONFLICT(external_reference) DO NOTHING`, [userId, seconds, externalReference]);
  if (result.rowCount) {
    await client.query(`UPDATE time_wallets SET balance_seconds=balance_seconds+$2,updated_at=now() WHERE user_id=$1`, [userId, seconds]);
  } else {
    const prior = await client.query<{ user_id: string; seconds: string }>(`SELECT user_id,seconds FROM time_wallet_entries WHERE external_reference=$1`, [externalReference]);
    if (prior.rows[0]?.user_id !== userId || Number(prior.rows[0]?.seconds) !== seconds) throw new Error("payment reference conflict");
  }
}
