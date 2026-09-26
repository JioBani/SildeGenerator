import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync} from 'node:fs';
import {dirname,resolve,join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..'),dir=join(root,'experiments/actor-binding'),out=join(dir,'output');
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
try{
 const options={viewport:{width:1000,height:820},deviceScaleFactor:1},source=await browser.newPage(options),bound=await browser.newPage(options);
 const requests=[],errors=[];bound.on('request',r=>requests.push(r.url()));for(const p of [source,bound])p.on('pageerror',e=>errors.push(e.message));
 await source.goto(pathToFileURL(join(root,'experiments/actor-contact/stage.html')).href);
 await bound.goto(pathToFileURL(join(dir,'stage.html')).href);
 await source.waitForFunction(()=>!!window.ContactStage);await bound.waitForFunction(()=>!!window.ContactStage);
 assert(!requests.some(p=>p.includes('layered-motion')||p.includes('gsap')));
 const results=[];
 for(const scene of ['retain','curtain']){
   await source.evaluate(n=>ContactStage.load(n),scene);await bound.evaluate(n=>ContactStage.load(n),scene);
   for(let frame=0;frame<240;frame++){
     const t=frame/30;
     const a=await source.evaluate(t=>ContactStage.draw(t).rendered,t),b=await bound.evaluate(t=>ContactStage.draw(t).rendered,t);
     assert.deepEqual(a,b,scene+':rendered-contact:'+frame);
   }
   const times=[0,1.2,2.2,3.4,3.86,4.8,5.9,7.6,0];
   for(const t of times){
     await source.evaluate(t=>ContactStage.draw(t),t);await bound.evaluate(t=>ContactStage.draw(t),t);
     assert.ok((await source.screenshot()).equals(await bound.screenshot()),scene+':pixel_mismatch:'+t);
   }
   results.push({scene,rendered_contact_equal_frames:240,pixel_exact_samples:times});
 }
 const {intent,scene}=JSON.parse(readFileSync(join(out,'director-fixture.json'),'utf8'));
 const selection=await bound.evaluate(({intent,scene})=>runActorIntent(intent,scene),{intent,scene});
 assert.equal(selection.admission,'RESEARCH_ONLY');assert.equal(selection.production_ready,false);
 await bound.evaluate(()=>ContactStage.draw(5.9));await bound.screenshot({path:join(out,'director-original.png')});
 scene.objects[1].position=[315,360];scene.objects[2].position=[370,360];
 await bound.evaluate(({intent,scene})=>runActorIntent(intent,scene),{intent,scene});
 const before=await bound.evaluate(()=>ContactStage.draw(0)),after=await bound.evaluate(()=>ContactStage.draw(7));
 assert.deepEqual(before.rendered.prop,{x:315,y:360});assert.deepEqual(after.rendered.prop,{x:370,y:360});
 assert.deepEqual(after.rendered.hand,after.rendered.prop);
 await bound.screenshot({path:join(out,'director-moved-target.png')});
 assert.deepEqual(errors,[]);
 const report={checked_at:new Date().toISOString(),results,old_scene_module_loaded:false,director_target_resolution:true,
   source_hashes:Object.fromEntries(['rig.js','director.js','stage.html','output/actor-data.js'].map(p=>[p,hash(join(dir,p))])),
   human_review:'PENDING',production_ready:false,scope:'Standard authored actor only; explicit director intent fixture, not a live model or production planner call'};
 writeFileSync(join(out,'playback-audit.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}finally{await browser.close();}
