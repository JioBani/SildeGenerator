import { chromium } from '@playwright/test';
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const out = join(root, 'experiments/actor-motion-runtime/output/astra-character');
mkdirSync(out, {recursive:true});
const browser = await chromium.launch({headless:true, executablePath:process.env.PLAYWRIGHT_BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
try {
  const page = await browser.newPage({viewport:{width:600,height:760},deviceScaleFactor:1});
  await page.setContent('<style>html,body{margin:0;background:transparent}svg{display:block;width:600px;height:760px}</style><svg id="art" xmlns="http://www.w3.org/2000/svg" viewBox="436 180 600 760"></svg>');
  const inputs = ['video-generator/hyperframes-runtime/node_modules/gsap/dist/gsap.min.js','experiments/layered-motion/performance.js','experiments/layered-motion/actor.js'];
  for (const path of inputs.slice(0,2)) await page.addScriptTag({path:join(root,path)});
  // Author a separated neutral stance using the existing vector artwork, not guessed image landmarks.
  await page.evaluate(() => {
    const original = window.ActorMotion.sample;
    window.ActorMotion.sample = (...args) => ({...original(...args),
      elbowL:{x:-145,y:-392}, handL:{x:-175,y:-300}, elbowR:{x:145,y:-392}, handR:{x:175,y:-300}});
  });
  await page.addScriptTag({path:join(root,inputs[2])});
  const cfg = await page.evaluate(() => {
    document.querySelector('#environment').remove();
    document.querySelector('#contact-shadows').remove();
    const s = window.ActorRenderer.state;
    const p = (q) => [q.x+300,q.y+730];
    const rows = [
      ['root',null,s.hip],['hip','root',s.hip],['torso','hip',{x:0,y:-456}],['neck','torso',s.neck],
      ['right_shoulder','torso',s.shoulderL],['right_elbow','right_shoulder',s.elbowL],['right_hand','right_elbow',s.handL],
      ['left_shoulder','torso',s.shoulderR],['left_elbow','left_shoulder',s.elbowR],['left_hand','left_elbow',s.handR],
      ['right_hip','root',s.hipL],['right_knee','right_hip',s.kneeL],['right_foot','right_knee',s.ankleL],
      ['left_hip','root',s.hipR],['left_knee','left_hip',s.kneeR],['left_foot','left_knee',s.ankleR]];
    return {width:600,height:760,skeleton:rows.map(([name,parent,loc])=>({name,parent,loc:p(loc)}))};
  });
  await page.locator('#art').screenshot({path:join(out,'texture.png'),omitBackground:true});
  writeFileSync(join(out,'char_cfg.yaml'),JSON.stringify(cfg,null,2));
  writeFileSync(join(out,'source.json'),JSON.stringify({actor:'Existing Astra vector test actor',
    coordinate_origin:'EXISTING_VECTOR_GEOMETRY_WITH_SEPARATED_ARM_REST_POSE',
    automatic_joint_detection:false,production_ready:false,
    sources:Object.fromEntries(inputs.map(p=>[p,createHash('sha256').update(readFileSync(join(root,p))).digest('hex')]))},null,2));
  console.log('Exported existing vector actor and exact authored joint coordinates');
} finally {await browser.close();}
