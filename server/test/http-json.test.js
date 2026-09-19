const assert = require("node:assert/strict");
const http = require("node:http");
const test = require("node:test");

const { postJson } = require("../dist/worker/runners/http-json.js");
const { failedStage, userFacingRunnerError } = require("../dist/worker/runner-error.js");

function listen(handler) {
  const server = http.createServer(handler);
  return new Promise((resolve) => server.listen(0, "127.0.0.1", () => resolve(server)));
}

test("postJson waits for delayed response headers", async (context) => {
  const server = await listen((request, response) => {
    request.resume();
    setTimeout(() => {
      response.writeHead(200, { "content-type": "application/json" });
      response.end('{"success":true}');
    }, 150);
  });
  context.after(() => server.close());
  const address = server.address();

  const result = await postJson(`http://127.0.0.1:${address.port}/render`, { job: "test" }, new AbortController().signal);

  assert.equal(result.status, 200);
  assert.deepEqual(JSON.parse(result.text), { success: true });
});

test("postJson obeys the job AbortSignal", async (context) => {
  const server = await listen((request) => request.resume());
  context.after(() => server.close());
  const address = server.address();
  const controller = new AbortController();
  setTimeout(() => controller.abort(), 30);

  await assert.rejects(
    postJson(`http://127.0.0.1:${address.port}/render`, {}, controller.signal),
    (error) => error.name === "AbortError",
  );
});

test("runner errors identify the failed stage and hide transport jargon", () => {
  const stage = failedStage([
    { stage: "scene_planning", status: "completed" },
    { stage: "image_generation", status: "failed" },
  ]);

  assert.equal(stage, "image_generation");
  assert.match(userFacingRunnerError(new Error("fetch failed"), stage), /^이미지 생성 단계/);
  assert.doesNotMatch(userFacingRunnerError(new Error("fetch failed"), stage), /fetch failed/);
  assert.match(
    userFacingRunnerError(new Error("codex returned an invalid scene plan: scene narration must preserve the entire original script"), "scene_planning"),
    /대본 일부가 누락/,
  );
});
