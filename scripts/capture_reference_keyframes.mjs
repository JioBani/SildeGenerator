import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import puppeteer from "/app/hyperframes-runtime/node_modules/puppeteer-core/lib/puppeteer/puppeteer-core.js";

const [url, outputDirectory, intervalText = "15"] = process.argv.slice(2);
if (!url || !outputDirectory) {
  throw new Error("usage: capture_reference_keyframes.mjs <url> <output-dir> [interval-seconds]");
}

const intervalSeconds = Number(intervalText);
if (!Number.isFinite(intervalSeconds) || intervalSeconds <= 0) {
  throw new Error("interval-seconds must be a positive number");
}

await fs.mkdir(outputDirectory, {recursive: true});
const browser = await puppeteer.launch({
  executablePath: process.env.HYPERFRAMES_BROWSER_PATH || "/usr/bin/chromium",
  headless: true,
  args: ["--no-sandbox", "--disable-dev-shm-usage", "--autoplay-policy=no-user-gesture-required"],
});

try {
  const page = await browser.newPage();
  await page.setViewport({width: 1920, height: 1080, deviceScaleFactor: 1});
  await page.goto(url, {waitUntil: "domcontentloaded", timeout: 60_000});
  await page.waitForSelector("video", {timeout: 60_000});
  await page.evaluate(async () => {
    const video = document.querySelector("video");
    if (!video) throw new Error("video element missing");
    video.muted = true;
    if (video.readyState < 1) {
      await new Promise((resolve) => video.addEventListener("loadedmetadata", resolve, {once: true}));
    }
  });

  const duration = await page.$eval("video", (video) => video.duration);
  if (!Number.isFinite(duration) || duration <= 0) throw new Error("video duration unavailable");
  const timestamps = [];
  for (let seconds = 0; seconds < duration; seconds += intervalSeconds) timestamps.push(seconds);
  if (timestamps.at(-1) < duration - 1) timestamps.push(Math.max(0, duration - 0.5));

  const captures = [];
  for (const seconds of timestamps) {
    const seekUrl = new URL(url);
    if (seekUrl.pathname.includes("/embed/")) {
      seekUrl.searchParams.set("start", `${Math.floor(seconds)}`);
      seekUrl.searchParams.set("autoplay", "1");
    } else {
      seekUrl.searchParams.set("t", `${Math.floor(seconds)}s`);
    }
    await page.goto(seekUrl.href, {waitUntil: "domcontentloaded", timeout: 60_000});
    await page.waitForSelector("video", {timeout: 60_000});
    await page.$eval("video", async (video, target) => {
      video.muted = true;
      await video.play().catch(() => undefined);
      if (Math.abs(video.currentTime - target) > 2) video.currentTime = target;
      await new Promise((resolve, reject) => {
        const started = performance.now();
        const poll = () => {
          if (Math.abs(video.currentTime - target) < 1.5 && video.readyState >= 2) {
            video.pause();
            resolve();
            return;
          }
          if (performance.now() - started > 30_000) {
            reject(new Error(`seek timeout at ${target}s; current=${video.currentTime}; ready=${video.readyState}`));
            return;
          }
          setTimeout(poll, 100);
        };
        poll();
      });
    }, seconds);
    await new Promise((resolve) => setTimeout(resolve, 250));
    const video = await page.$("video");
    if (!video) throw new Error("video element disappeared");
    const filename = `frame-${String(Math.round(seconds)).padStart(4, "0")}.png`;
    await video.screenshot({path: path.join(outputDirectory, filename)});
    captures.push({seconds, filename});
  }

  const metadata = await page.evaluate(() => ({
    title: document.title,
    canonicalUrl: document.querySelector('link[rel="canonical"]')?.href || location.href,
  }));
  await fs.writeFile(path.join(outputDirectory, "capture-manifest.json"), JSON.stringify({
    sourceUrl: url,
    ...metadata,
    duration,
    intervalSeconds,
    captures,
  }, null, 2));
  process.stdout.write(JSON.stringify({duration, captureCount: captures.length, outputDirectory}));
} finally {
  await browser.close();
}
