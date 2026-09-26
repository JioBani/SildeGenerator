import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {existsSync, mkdirSync, readFileSync, writeFileSync} from 'node:fs';
import {dirname, join, resolve, relative} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const dir = join(root, 'experiments/actor-binding');
const version = process.argv.find(a => a.startsWith('--version='))?.slice(10) || 'planner-v1';
assert.match(version, /^planner-v[1-9][0-9]*$/);
const input = join(dir, 'output', version), out = join(input, 'render');
const hash = p => createHash('sha256').update(readFileSync(p)).digest('hex');
const receipt = JSON.parse(readFileSync(join(input, 'receipt.json'), 'utf8'));
for (const [path, sha] of Object.entries(receipt.artifacts)) assert.equal(hash(join(input, path)), sha);
for (const [path, sha] of Object.entries(receipt.sources)) assert.equal(hash(join(root, path)), sha);
const schemaValidation = JSON.parse(readFileSync(join(input, 'schema-validation.json'), 'utf8'));
assert.equal(schemaValidation.status, 'PASS');
for (const [path, sha] of Object.entries(schemaValidation.artifacts)) assert.equal(hash(join(input, path)), sha);
assert.equal(receipt.live_model_calls, 0);
const packets = JSON.parse(readFileSync(join(input, 'execution-packets.json'), 'utf8'));
assert.equal(packets.length, 2);
assert(!existsSync(out), 'Choose a new planner version; do not replace captured evidence');
mkdirSync(out);
const browser = await chromium.launch({headless: true,
  executablePath: process.env.PLAYWRIGHT_BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
try {
  const page = await browser.newPage({viewport: {width: 1000, height: 820}, deviceScaleFactor: 1});
  const errors = [], requests = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('request', r => requests.push(r.url()));
  await page.route(/^https?:/, route => route.abort());
  await page.goto(pathToFileURL(join(dir, 'stage.html')).href);
  await page.waitForFunction(() => !!window.runActorIntent);
  const captures = [];
  for (const packet of packets) {
    assert.match(packet.scene.id, /^scene-[0-9]{3}$/);
    const folder = join(out, packet.scene.id);
    mkdirSync(folder);
    const selection = await page.evaluate(p => runActorIntent(p.intent, p.scene), packet);
    assert.equal(selection.admission, 'RESEARCH_ONLY');
    assert.equal(selection.production_ready, false);
    const trace = [], frames = Math.round(packet.intent.duration * 30);
    for (let frame = 0; frame < frames; frame++) {
      trace.push(await page.evaluate(t => ContactStage.draw(t), frame / 30));
      await page.locator('#art').screenshot({path: join(folder, `frame-${String(frame).padStart(3, '0')}.png`)});
    }
    const target = packet.scene.objects.find(o => o.id === packet.intent.target_id).position;
    const destination = packet.scene.objects.find(o => o.id === packet.intent.destination_id)?.position || target;
    const pair = p => [p.x, p.y];
    const distance = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
    assert(distance(pair(trace[0].rendered.prop), target) < .001);
    assert(distance(pair(trace.at(-1).rendered.prop), destination) < .001);
    const attached = trace.filter(t => t.state.contact.attached);
    assert(attached.length > 0);
    const contactError = Math.max(...attached.map(t => distance(pair(t.rendered.hand), pair(t.rendered.prop))));
    const footDrift = Math.max(...trace.flatMap(t => t.rendered.feet.map((f, i) => distance(f, trace[0].rendered.feet[i]))));
    assert(contactError < .001 && footDrift < .001);
    assert.equal(new Set(attached.map(t => t.rendered.local_attachment)).size, 1);
    for (const t of attached) {
      assert.equal(t.rendered.parent, packet.intent.side + '-object-slot');
      assert(t.rendered.prop_before_fingers && t.rendered.active_arm_in_front_of_torso);
    }
    const finalPixels = await page.screenshot();
    await page.evaluate(() => ContactStage.draw(0));
    await page.evaluate(t => ContactStage.draw(t), (frames - 1) / 30);
    assert(finalPixels.equals(await page.screenshot()), 'reverse seek must preserve rendered pixels');
    const stable = await page.locator('#art').evaluate(e => e.outerHTML);
    const rejected = await page.evaluate(p => {
      try { runActorIntent({...p.intent, action: 'walk'}, p.scene); return false; }
      catch (e) { return e.message === 'action_not_in_research_catalog'; }
    }, packet);
    assert(rejected);
    assert.equal(await page.locator('#art').evaluate(e => e.outerHTML), stable);
    const sourceFiles = ['rig.js', 'director.js', 'stage.html', 'output/actor-data.js',
      '../actor-performance/performance.js', '../actor-performance/asset-player.js',
      '../actor-contact/contact.js', '../actor-contact/stage.js'];
    const snapshots = {};
    for (const [index, file] of sourceFiles.entries()) {
      const path = join(dir, file), name = `source-${index}.txt`;
      writeFileSync(join(folder, name), readFileSync(path));
      snapshots[relative(root, path).replaceAll('\\', '/')] = {file: name, sha256: hash(path)};
    }
    writeFileSync(join(folder, 'trace.json'), JSON.stringify(trace));
    const capture = {packet, request: selection.request, events: selection.events, snapshots, fps: 30,
      frame_count: frames, contact_error_px: contactError, foot_drift_px: footDrift,
      prop_start: target, prop_end: destination, reverse_seek_exact: true, unsupported_action_preserves_stage: true,
      trace_sha256: hash(join(folder, 'trace.json')), plan_receipt_sha256: hash(join(input, 'receipt.json')),
      frame_hashes: Array.from({length: frames}, (_, i) => hash(join(folder, `frame-${String(i).padStart(3, '0')}.png`))),
      director_output_origin: receipt.director_output_origin, production_ready: false, human_review: 'PENDING'};
    writeFileSync(join(folder, 'capture.json'), JSON.stringify(capture, null, 2));
    captures.push({scene_id: packet.scene.id, contact_error_px: contactError, foot_drift_px: footDrift});
    console.log(JSON.stringify(captures.at(-1)));
  }
  assert.deepEqual(errors, []);
  assert(!requests.some(url => /^https?:/.test(url)));
  writeFileSync(join(out, 'audit.json'), JSON.stringify({captures, errors, network_requests: 0,
    scope: 'Real create_plan transport/compiler -> production pack -> research actor renderer; authored response fixture, not AI selection',
    human_review: 'PENDING', production_ready: false}, null, 2));
} finally { await browser.close(); }
