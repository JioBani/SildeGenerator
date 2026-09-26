import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdirSync, readFileSync, writeFileSync} from 'node:fs';
import {dirname, join, resolve} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const output = join(root, 'experiments/actor-d-upper-body/output');
const d = join(root, 'experiments/light-pollution-story-asset-v1/D/project');
const f = join(root, 'experiments/light-pollution-story-asset-v1/F-master-actor-v1/assets');
const hash = path => createHash('sha256').update(readFileSync(path)).digest('hex');
const candidate = JSON.parse(readFileSync(join(root, 'docs/actor-assets/d-nightlight-candidate.json'), 'utf8'));
for (const item of [candidate.video, candidate.human_review, candidate.program, ...Object.values(candidate.layers)]) {
  assert.equal(hash(join(root, item.path)), item.sha256, 'Approved D source changed: ' + item.path);
}
const paths = {
  body: join(d, 'assets/person-body.png'),
  torso: join(root, 'experiments/actor-d-upper-body/assets/torso-underpainting-v1.png'),
  upper: join(f, 'upper-arm.png'), forearm: join(f, 'forearm.png'), hand: join(f, 'hand-relaxed.png'),
};
const images = Object.fromEntries(Object.entries(paths).map(([key, path]) => [key, 'data:image/png;base64,' + readFileSync(path).toString('base64')]));
const dImages = {};
for (const name of ['person-body.png', 'person-head-neutral.png', 'person-head-notice.png', 'person-head-squint-v3.png', 'person-neck-overlap-v4b.png']) {
  dImages['assets/' + name] = 'data:image/png;base64,' + readFileSync(join(d, 'assets', name)).toString('base64');
}
const browser = await chromium.launch({headless: true,
  executablePath: process.env.PLAYWRIGHT_BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
try {
  const page = await browser.newPage();
  await page.goto(pathToFileURL(join(d, 'index.html')).href);
  const source = await page.evaluate(data => {
    const extract = selector => {
      const node = document.querySelector(selector).cloneNode(true);
      for (const image of node.querySelectorAll('img')) {
        const path = image.getAttribute('src');
        if (!data[path]) throw Error('Unexpected D source image');
        image.setAttribute('src', data[path]);
      }
      return node.outerHTML;
    };
    let css = document.querySelector('style').textContent;
    for (const [path, uri] of Object.entries(data)) css = css.replaceAll(path, uri);
    return {css, head: extract('.head'), collar: extract('.collar-front')};
  }, dImages);
  const data = {source, images, approved_source: candidate,
    asset_hashes: Object.fromEntries(Object.entries(paths).map(([key, path]) => [key, hash(path)])),
    state: 'D_DERIVATIVE_RESEARCH_ONLY', inherited_approval: false, production_ready: false};
  mkdirSync(output, {recursive: true});
  writeFileSync(join(output, 'actor-data.js'), 'window.DUpperSource=' + JSON.stringify(data) + ';');
  console.log(JSON.stringify({output, original_D_hashes_verified: true, source_assets: Object.keys(paths)}));
} finally { await browser.close(); }
