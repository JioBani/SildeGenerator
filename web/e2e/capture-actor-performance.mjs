import {chromium} from '@playwright/test';
import {createHash} from 'node:crypto';
import {mkdirSync,readFileSync,writeFileSync,existsSync} from 'node:fs';
import {dirname,resolve,join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const dir=join(root,'experiments/actor-performance');
const mode=process.argv.includes('--video')?'video':'inspect';
const output=join(dir,'output',mode==='video'?'v1':'inspection');
mkdirSync(output,{recursive:true});
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const candidate=JSON.parse(readFileSync(join(root,'docs/actor-assets/d-nightlight-candidate.json'),'utf8'));
for(const key of ['video','human_review','program']) if(hash(join(root,candidate[key].path))!==candidate[key].sha256)throw Error('Approved D changed');
const browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
try{
  const page=await browser.newPage({viewport:{width:1000,height:820},deviceScaleFactor:1});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(pathToFileURL(join(dir,'stage.html')).href);
  await page.waitForFunction(()=>!!window.PerformanceStage);
  for(const scene of ['result','glare']){
    const folder=join(output,scene);mkdirSync(folder,{recursive:true});
    if(mode==='video' && existsSync(join(folder,'trace.json')))throw Error('Do not overwrite a prior capture');
    await page.evaluate(scene=>window.PerformanceStage.load(scene),scene);
    const times=mode==='video'?Array.from({length:180},(_,i)=>i/30):[0,.85,1.2,1.8,2.8,3.5,5.5];
    const trace=[];
    for(let i=0;i<times.length;i++){
      const state=await page.evaluate(t=>{
        const s=window.PerformanceStage.draw(t);
        const point=e=>{const m=e.getCTM();return [m.e,m.f];};
        return {time:t,performance:s.performance,headAngle:s.headAngle,torsoAngle:s.torsoAngle,
          shoulderL:s.shoulderL,shoulderR:s.shoulderR,elbowL:s.elbowL,elbowR:s.elbowR,handL:s.handL,handR:s.handR,
          ankleL:s.ankleL,ankleR:s.ankleR,pupilOffsets:s.pupilOffsets,eyesOpen:s.eyesOpen,
          renderedPalm:{left:point(window.PerformanceStage.parts.left.hand),right:point(window.PerformanceStage.parts.right.hand)}};
      },times[i]);
      trace.push(state);
      await page.locator('#art').screenshot({path:join(folder,`frame-${String(i).padStart(3,'0')}.png`)});
    }
    const a=await page.evaluate(()=>{window.PerformanceStage.draw(3.5);return document.querySelector('#art').outerHTML;});
    await page.evaluate(()=>window.PerformanceStage.draw(.2));
    const b=await page.evaluate(()=>{window.PerformanceStage.draw(3.5);return document.querySelector('#art').outerHTML;});
    if(a!==b)throw Error('Non-deterministic reverse seek');
    writeFileSync(join(folder,'trace.json'),JSON.stringify(trace,null,2));
    const spec=await page.evaluate(()=>({request:window.PerformanceStage.request,events:window.PerformanceStage.events,spec:window.ActorPerformance.spec}));
    writeFileSync(join(folder,'capture.json'),JSON.stringify({...spec,frame_count:times.length,fps:30,render_errors:errors,
      source_hashes:Object.fromEntries(['performance.js','skin.js','stage.html','../layered-motion/actor.js','../layered-motion/performance.js'].map(p=>[p,hash(join(dir,p))])),
      production_ready:false,human_review:'PENDING',paid_api_calls:0},null,2));
    // Save editable vector assembly with independent named limb and face groups.
    writeFileSync(join(folder,'assembly.svg'),await page.locator('#art').evaluate(e=>e.outerHTML));
  }
  if(errors.length)throw Error(errors.join('\n'));
  console.log(JSON.stringify({mode,output,page_errors:errors}));
}finally{await browser.close();}
