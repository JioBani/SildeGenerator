import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import test from "node:test";

test("setup validates, stores atomically, and never reads a secret back", async () => {
  const runtime = await mkdtemp(path.join(tmpdir(), "slidegen-setup-"));
  const child = spawn(process.execPath, [path.resolve("server.mjs")], { env: { ...process.env, RUNTIME_DIR: runtime }, stdio: "ignore" });
  try {
    for (let count = 0; count < 50; count++) { try { if ((await fetch("http://127.0.0.1:8090/api/setup/status")).ok) break; } catch {} await new Promise((resolve) => setTimeout(resolve, 25)); }
    const invalid = await fetch("http://127.0.0.1:8090/api/setup/validate", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ mode: "live", voiceProvider: "elevenlabs", elevenLabsApiKey: "bad" }) });
    assert.equal(invalid.status, 400);
    const page = await (await fetch("http://127.0.0.1:8090/")).text();
    assert.match(page, /name="elevenLabsStability"/);
    assert.match(page, /name="elevenLabsSimilarity"/);
    assert.match(page, /name="elevenLabsSpeed"/);
    assert.doesNotMatch(page, /auth\.json|type="file"/);
    const secret = "example_key_for_test_only_123456";
    const saved = await fetch("http://127.0.0.1:8090/api/setup/save", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ mode: "live", voiceProvider: "elevenlabs", elevenLabsApiKey: secret, webPort: 8080, imageConcurrency: 4, voiceConcurrency: 2, fps: 24, retentionHours: 720, elevenLabsStability: 0.55, elevenLabsSimilarity: 0.65, elevenLabsSpeed: 0.8 }) });
    assert.equal(saved.status, 200);
    assert.equal((await saved.json()).secretReadable, false);
    const statusResponse = await fetch("http://127.0.0.1:8090/api/setup/status");
    const statusText = await statusResponse.text();
    assert.equal(statusText.includes(secret), false);
    const runnerEnv = await readFile(path.join(runtime, "runner.env"), "utf8");
    assert.equal(runnerEnv.includes(secret), true);
    assert.match(runnerEnv, /ELEVENLABS_STABILITY=0\.55/);
    assert.match(runnerEnv, /ELEVENLABS_SIMILARITY_BOOST=0\.65/);
    assert.match(runnerEnv, /ELEVENLABS_SPEED=0\.8/);
    assert.equal((await readFile(path.join(runtime, "bootstrap-state.json"), "utf8")).includes(secret), false);
  } finally { child.kill(); await rm(runtime, { recursive: true, force: true }); }
});
