import Redis from 'ioredis';
import { Queue } from 'bullmq';
import { redisConnection } from '../config/app-config';
import { RENDER_QUEUE } from '../shared/render-job';
// Run only while API and worker are stopped: submissions and completions must not race this repair.
async function main() {
  const redis = new Redis(redisConnection());
  const queue = new Queue(RENDER_QUEUE, { connection: redisConnection() });
  let removed = 0;
  try {
    const ids = await redis.smembers('limits:pending:global');
    for (const id of ids) {
      const job = await queue.getJob(id);
      const state = job ? await job.getState() : 'unknown';
      if (!['completed', 'failed', 'unknown'].includes(state)) continue;
      let cursor = '0';
      do {
        const page = await redis.scan(cursor, 'MATCH', 'limits:pending:*', 'COUNT', 100);
        cursor = page[0];
        for (const key of page[1]) await redis.srem(key, id);
      } while (cursor !== '0');
      removed++;
    }
    console.log(JSON.stringify({ removed }));
  } finally { await queue.close(); redis.disconnect(); }
}
void main();
