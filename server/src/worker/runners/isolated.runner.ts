import { request } from 'node:http';
import { writeFile } from 'node:fs/promises';
import { Injectable } from '@nestjs/common';
import type { RunContext, RunnerResult, VideoRunner } from './video-runner';
@Injectable()
export class IsolatedRunner implements VideoRunner {
  async run({ paths, signal, codexModel, codexReasoningEffort, codexFastMode, imageModel, continuityEnabled, imageStyle, voiceSettings, harnessId, harnessSnapshot }: RunContext): Promise<RunnerResult> {
    const { readFile } = await import('node:fs/promises');
    const payload = JSON.stringify({
      scenario: await readFile(paths.scenario, 'utf8'),
      codex_model: codexModel,
      codex_reasoning_effort: codexReasoningEffort,
      codex_fast_mode: codexFastMode,
      image_model: imageModel,
      continuity_enabled: continuityEnabled,
      image_style: imageStyle,
      voice_settings: {
        provider: voiceSettings.provider, model: voiceSettings.model,
        voice_id: voiceSettings.voiceId, voice_name: voiceSettings.voiceName,
        rate: voiceSettings.rate, pitch: voiceSettings.pitch, volume: voiceSettings.volume,
        stability: voiceSettings.stability, similarity_boost: voiceSettings.similarityBoost,
        speed: voiceSettings.speed, version: voiceSettings.version,
      },
      harness_id: harnessId,
      harness_snapshot: harnessSnapshot,
    });
    const data = await new Promise<Buffer>((resolve, reject) => {
      const req = request({ socketPath: '/broker/broker.sock', path: '/render', method: 'POST', signal,
        headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload) } }, res => {
        if (res.statusCode !== 200) { res.resume(); reject(new Error('isolated renderer rejected request')); return; }
        const chunks: Buffer[] = []; let size = 0;
        res.on('data', (chunk: Buffer) => {
          size += chunk.length;
          if (size > 32 * 1024 * 1024) res.destroy(new Error('video too large'));
          else chunks.push(chunk);
        });
        res.on('error', reject);
        res.on('end', () => resolve(Buffer.concat(chunks)));
      });
      req.on('error', reject); req.end(payload);
    });
    if (data.length < 12 || data.subarray(4, 8).toString() !== 'ftyp') throw new Error('invalid video');
    await writeFile(paths.video, data, { flag: 'wx' });
    return { success: true, video_path: paths.video, message: 'isolated legacy runner', stages: [], usage: [], assets: [], prompts: [] };
  }
}
