import http from "node:http";
import { open, readFile, rename, unlink } from "node:fs/promises";
import path from "node:path";

const runtime = path.resolve(process.env.RUNTIME_DIR || "/runtime");
const maxBody = 64 * 1024;
const headers = {
  "Cache-Control": "no-store",
  "Content-Security-Policy": "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
  "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Referrer-Policy": "no-referrer",
};
const edgeVoices = ["ko-KR-InJoonNeural", "ko-KR-SunHiNeural", "ko-KR-HyunsuMultilingualNeural"];
const allowedProviders = ["mock", "microsoft_edge", "elevenlabs"];
const pageHtml = await readFile(new URL("./index.html", import.meta.url), "utf8");

function numeric(input, key, fallback, minimum, maximum, errors, label) {
  const value = Number(input[key] ?? fallback);
  if (!Number.isFinite(value) || value < minimum || value > maximum) errors.push(`${label} 값은 ${minimum}~${maximum} 범위여야 합니다.`);
  return value;
}

function validate(input) {
  const mode = input.mode === "live" ? "live" : input.mode === "mock" ? "mock" : null;
  const voiceProvider = allowedProviders.includes(input.voiceProvider) ? input.voiceProvider : null;
  const errors = [];
  if (!mode) errors.push("실행 모드를 선택해 주세요.");
  if (!voiceProvider) errors.push("음성 공급자를 선택해 주세요.");
  if (voiceProvider === "elevenlabs" && !/^[A-Za-z0-9_-]{20,}$/.test(String(input.elevenLabsApiKey || ""))) errors.push("ElevenLabs API key 형식을 확인해 주세요.");
  if (voiceProvider === "microsoft_edge" && !edgeVoices.includes(input.edgeVoice)) errors.push("지원하는 한국어 Edge voice를 선택해 주세요.");
  for (const [key, pattern] of [["edgeRate", /^[+-](?:100|[0-9]{1,2})%$/], ["edgePitch", /^[+-](?:100|[0-9]{1,2})Hz$/], ["edgeVolume", /^[+-](?:100|[0-9]{1,2})%$/]]) {
    if (voiceProvider === "microsoft_edge" && !pattern.test(String(input[key] || ""))) errors.push(`${key} 형식을 확인해 주세요.`);
  }
  const webPort = numeric(input, "webPort", 8080, 1024, 65535, errors, "웹 포트");
  const imageConcurrency = numeric(input, "imageConcurrency", 8, 1, 16, errors, "이미지 동시성");
  const voiceConcurrency = numeric(input, "voiceConcurrency", 2, 1, 8, errors, "음성 동시성");
  const fps = numeric(input, "fps", 24, 24, 30, errors, "영상 FPS");
  const retentionHours = numeric(input, "retentionHours", 720, 1, 8760, errors, "작업 보존시간");
  if (![webPort, imageConcurrency, voiceConcurrency, fps, retentionHours].every(Number.isInteger)) errors.push("포트·동시성·FPS·보존시간은 정수여야 합니다.");
  if (![24, 25, 30].includes(fps)) errors.push("영상 FPS는 24, 25, 30 중 하나여야 합니다.");
  const elevenLabsStability = numeric(input, "elevenLabsStability", 0.6, 0, 1, errors, "Stability");
  const elevenLabsSimilarity = numeric(input, "elevenLabsSimilarity", 0.6, 0, 1, errors, "Similarity");
  const elevenLabsSpeed = numeric(input, "elevenLabsSpeed", 0.7, 0.7, 1.2, errors, "Speed");
  return { errors, value: {
    mode, voiceProvider, webPort, imageConcurrency, voiceConcurrency, fps, retentionHours,
    edgeVoice: input.edgeVoice || "ko-KR-InJoonNeural", edgeRate: input.edgeRate || "-30%", edgePitch: input.edgePitch || "+0Hz", edgeVolume: input.edgeVolume || "+0%",
    elevenLabsApiKey: String(input.elevenLabsApiKey || ""), elevenLabsVoiceId: String(input.elevenLabsVoiceId || "nPczCjzI2devNBz1zQrb"),
    elevenLabsVoiceName: String(input.elevenLabsVoiceName || "Brian"), elevenLabsModel: String(input.elevenLabsModel || "eleven_flash_v2_5"),
    elevenLabsStability, elevenLabsSimilarity, elevenLabsSpeed,
  }};
}

const envValue = (value) => String(value).replace(/[\r\n\0]/g, "");

async function atomicWrite(file, content) {
  const target = path.join(runtime, file);
  const temporary = `${target}.${process.pid}.tmp`;
  const handle = await open(temporary, "w", 0o600);
  try {
    await handle.writeFile(content, "utf8");
    await handle.sync();
    await handle.close();
    await rename(temporary, target);
  } catch (error) {
    await handle.close().catch(() => {});
    await unlink(temporary).catch(() => {});
    throw error;
  }
}

async function save(value) {
  const elevenLabsKeyName = "ELEVENLABS_" + "API_KEY";
  const compose = [
    `RUNNER_MODE=${value.mode}`, `IMAGE_PROVIDER=${value.mode === "live" ? "oauth" : "mock"}`, `VOICE_PROVIDER=${value.voiceProvider}`,
    `WEB_PORT=${value.webPort}`, `IMAGE_TASK_CONCURRENCY=${value.imageConcurrency}`, `VOICE_TASK_CONCURRENCY=${value.voiceConcurrency}`,
    `VIDEO_FPS=${value.fps}`, `JOB_RETENTION_HOURS=${value.retentionHours}`, `ELEVENLABS_CONFIGURED=${value.voiceProvider === "elevenlabs"}`,
    `MICROSOFT_EDGE_VOICE=${envValue(value.edgeVoice)}`, `MICROSOFT_EDGE_RATE=${envValue(value.edgeRate)}`, `MICROSOFT_EDGE_PITCH=${envValue(value.edgePitch)}`, `MICROSOFT_EDGE_VOLUME=${envValue(value.edgeVolume)}`,
    `ELEVENLABS_VOICE_ID=${envValue(value.elevenLabsVoiceId)}`, `ELEVENLABS_VOICE_NAME=${envValue(value.elevenLabsVoiceName)}`, `ELEVENLABS_MODEL_ID=${envValue(value.elevenLabsModel)}`,
  ].join("\n") + "\n";
  const runner = value.voiceProvider === "elevenlabs" ? [
    `${elevenLabsKeyName}=${envValue(value.elevenLabsApiKey)}`, `ELEVENLABS_VOICE_ID=${envValue(value.elevenLabsVoiceId)}`,
    `ELEVENLABS_VOICE_NAME=${envValue(value.elevenLabsVoiceName)}`, `ELEVENLABS_MODEL_ID=${envValue(value.elevenLabsModel)}`,
    `ELEVENLABS_STABILITY=${value.elevenLabsStability}`, `ELEVENLABS_SIMILARITY_BOOST=${value.elevenLabsSimilarity}`, `ELEVENLABS_SPEED=${value.elevenLabsSpeed}`,
  ].join("\n") + "\n" : "# No provider secret is required for this voice provider.\n";
  await atomicWrite("compose.user.env", compose);
  await atomicWrite("runner.env", runner);
  await atomicWrite("bootstrap-state.json", JSON.stringify({ schemaVersion: 1, configured: true, mode: value.mode, voiceProvider: value.voiceProvider, webPort: value.webPort, codexLogin: value.mode === "live" ? "required" : "not_required", configuredAt: new Date().toISOString() }, null, 2) + "\n");
  await atomicWrite("setup-complete", `${Date.now()}\n`);
}

function json(res, status, payload) {
  res.writeHead(status, { ...headers, "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(payload));
}
async function body(req) {
  let size = 0; const chunks = [];
  for await (const chunk of req) { size += chunk.length; if (size > maxBody) throw new Error("BODY_TOO_LARGE"); chunks.push(chunk); }
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}
async function statusPayload() {
  let state = { configured: false, codexLogin: "unknown" };
  try { state = JSON.parse(await readFile(path.join(runtime, "bootstrap-state.json"), "utf8")); } catch {}
  return { ...state, secretsReadable: false };
}

const server = http.createServer(async (req, res) => {
  try {
    if (req.method === "GET" && req.url === "/") { res.writeHead(200, { ...headers, "Content-Type": "text/html; charset=utf-8" }); return res.end(pageHtml); }
    if (req.method === "GET" && req.url === "/api/setup/schema") return json(res, 200, { modes: ["mock", "live"], voiceProviders: allowedProviders, edgeVoices });
    if (req.method === "GET" && req.url === "/api/setup/status") return json(res, 200, await statusPayload());
    if (req.method === "POST" && ["/api/setup/validate", "/api/setup/save"].includes(req.url)) {
      const result = validate(await body(req));
      if (result.errors.length) return json(res, 400, { ok: false, errors: result.errors });
      if (req.url.endsWith("save")) await save(result.value);
      return json(res, 200, { ok: true, configured: true, secretStored: result.value.voiceProvider === "elevenlabs", secretReadable: false });
    }
    return json(res, 404, { error: "not found" });
  } catch (error) {
    return json(res, error.message === "BODY_TOO_LARGE" ? 413 : 400, { error: error.message === "BODY_TOO_LARGE" ? "request body too large" : "invalid request" });
  }
});
server.listen(8090, "0.0.0.0");
