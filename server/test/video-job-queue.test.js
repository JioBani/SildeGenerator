const assert = require("node:assert/strict");
const test = require("node:test");
const { VideoJobQueueService, positionForJob } = require("../dist/queue/video-job-queue.service");

test("queue positions exclude active jobs and jobsAhead includes them", () => {
  const active = ["job-a"];
  const queued = ["job-b", "job-c", "job-d", "job-e"];
  assert.deepEqual(positionForJob(active, queued, "job-a"), { queuePosition: null, jobsAhead: 0 });
  assert.deepEqual(positionForJob(active, queued, "job-b"), { queuePosition: 1, jobsAhead: 1 });
  assert.deepEqual(positionForJob(active, queued, "job-e"), { queuePosition: 4, jobsAhead: 4 });
});

test("unknown and finished jobs do not receive an invented position", () => {
  assert.deepEqual(positionForJob(["job-a"], ["job-b"], "done"), { queuePosition: null, jobsAhead: null });
});

test("snapshot reports one active job and four ordered pending jobs", async () => {
  const now = Date.now();
  const jobs = (ids) => ids.map((id, index) => ({ id, timestamp: now - (index + 1) * 1000 }));
  const queue = {
    setGlobalConcurrency: async () => 1,
    getGlobalConcurrency: async () => 1,
    getActive: async () => jobs(["job-a"]),
    getPrioritized: async () => [],
    getWaiting: async () => jobs(["job-b", "job-c", "job-d"]),
    getDelayed: async () => jobs(["job-e"]),
  };
  const service = new VideoJobQueueService(queue);
  const snapshot = await service.snapshot("job-d");
  assert.equal(snapshot.activeJobs, 1);
  assert.equal(snapshot.queuedJobs, 4);
  assert.equal(snapshot.queuePosition, 3);
  assert.equal(snapshot.jobsAhead, 3);
  assert.ok(snapshot.oldestWaitMs >= 1000);
});

test("every API or worker instance applies global concurrency one", async () => {
  const applied = [];
  const queue = { setGlobalConcurrency: async (value) => applied.push(value) };
  await new VideoJobQueueService(queue).onModuleInit();
  await new VideoJobQueueService(queue).onModuleInit();
  assert.deepEqual(applied, [1, 1]);
});

test("queue lookup failure is fail-open", async () => {
  const queue = {
    getActive: async () => { throw new Error("redis unavailable"); },
    getPrioritized: async () => [], getWaiting: async () => [], getDelayed: async () => [], getGlobalConcurrency: async () => 1,
  };
  assert.equal(await new VideoJobQueueService(queue).safeSnapshot("job-a"), null);
});
