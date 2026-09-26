import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import {dirname,resolve,join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const version=process.argv.includes('--v3')?'v3':'v2';
const dir=join(root,'experiments/actor-performance'),out=join(dir,'output/standard-actor-'+version);
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const manifest=JSON.parse(readFileSync(join(out,'manifest.json'),'utf8'));
for(const part of manifest.parts)assert.equal(hash(join(out,part.path)),part.sha256);
assert.equal(hash(join(out,'assembled.svg')),manifest.assembly.rebuilt_sha256);
for(const [p,h] of Object.entries(manifest.source_hashes))assert.equal(hash(join(dir,p)),h);
const browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
try{
 const options={viewport:{width:1000,height:820},deviceScaleFactor:1};
 const source=await browser.newPage(options),reference=await browser.newPage(options),player=await browser.newPage(options);
 const errors=[];for(const p of [source,reference,player])p.on('pageerror',e=>errors.push(e.message));
 await source.goto(pathToFileURL(join(dir,'stage.html')).href);
 await source.waitForFunction(()=>!!window.PerformanceStage);
 const style='<style>body{margin:0;background:#edf3f5}svg{display:block;width:1000px;height:820px}</style>';
 await player.setContent(style+readFileSync(join(out,'assembled.svg'),'utf8'));
 for(const p of ['../../video-generator/hyperframes-runtime/node_modules/gsap/dist/gsap.min.js','../layered-motion/performance.js','performance.js','asset-player.js'])await player.addScriptTag({path:join(dir,p)});
 await player.evaluate(()=>window.actor=StandardActorPlayer.create(document.querySelector('svg'),ActorPerformance));
 const results=[];
 for(const scene of ['result','glare']){
   await source.evaluate(name=>PerformanceStage.load(name),scene);
   await player.evaluate(name=>window.action=actor.bind(ActorPerformance.fixtures[name]),scene);
   // Every output frame checks actual transformed palm positions, not just solver output.
   for(let frame=0;frame<180;frame++){
     const t=frame/30;
     const actual=await player.evaluate(t=>{
       action.draw(t);return ['left','right'].map(side=>{const m=document.querySelector('#'+side+'-palm').getCTM();return [m.a,m.b,m.c,m.d,m.e,m.f];});
     },t);
     const expected=await source.evaluate(t=>{
       PerformanceStage.draw(t);return ['left','right'].map(side=>{const m=document.querySelector('#'+side+'-palm').getCTM();return [m.a,m.b,m.c,m.d,m.e,m.f];});
     },t);
     assert.deepEqual(actual,expected,scene+':frame:'+frame);
   }
   const samples=[0,.85,1.2,1.8,2.8,3.5,5.5,0];
   for(let index=0;index<samples.length;index++){
     const t=samples[index];
     const svg=await source.evaluate(t=>{PerformanceStage.draw(t);return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 820">${document.querySelector('#art defs').outerHTML}${document.querySelector('#actor').outerHTML}</svg>`;},t);
     await reference.setContent(style+svg);await player.evaluate(t=>action.draw(t),t);
     const expected=await reference.screenshot(),actual=await player.screenshot();
     assert.ok(expected.equals(actual),scene+':pixel_mismatch_at:'+t);
     if(t===3.5)writeFileSync(join(out,scene+'-imported.png'),actual);
   }
   results.push({scene,rendered_palm_frames_equal:180,pixel_exact_samples:samples});
 }
 assert.deepEqual(errors,[]);
 const result={checked_at:new Date().toISOString(),results,asset_manifest_sha256:hash(join(out,'manifest.json')),player_sha256:hash(join(dir,'asset-player.js')),scope:'Same actor and performance code, independently loaded saved vector assembly; not another character or new design',human_review:'PENDING',production_ready:false};
 writeFileSync(join(out,'playback-audit.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}finally{await browser.close();}
