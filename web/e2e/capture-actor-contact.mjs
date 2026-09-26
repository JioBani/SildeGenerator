import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdirSync,readFileSync,writeFileSync,existsSync} from 'node:fs';
import {dirname,resolve,join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..'),dir=join(root,'experiments/actor-contact');
const version=process.argv.find(a=>a.startsWith('--version='))?.slice(10)||'v2';
if(!/^v[1-9][0-9]*$/.test(version))throw Error('invalid_output_version');
const video=process.argv.includes('--video'),out=join(dir,'output',video?version:'inspection');
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const d=JSON.parse(readFileSync(join(root,'docs/actor-assets/d-nightlight-candidate.json'),'utf8'));
for(const k of ['video','human_review','program'])assert.equal(hash(join(root,d[k].path)),d[k].sha256);
const browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
try{
 const page=await browser.newPage({viewport:{width:1000,height:820},deviceScaleFactor:1});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(join(dir,'stage.html')).href);await page.waitForFunction(()=>!!window.ContactStage);
 for(const scene of ['retain','curtain']){
   const folder=join(out,scene);mkdirSync(folder,{recursive:true});
   if(video&&existsSync(join(folder,'capture.json')))throw Error('Refusing existing output version');
   await page.evaluate(scene=>ContactStage.load(scene),scene);
   const times=video?Array.from({length:240},(_,i)=>i/30):[0,1.2,2.2,3.4,3.7,3.86,4.8,5.9,7.6];
   const trace=[];
   for(let i=0;i<times.length;i++){
     trace.push(await page.evaluate(t=>ContactStage.draw(t),times[i]));
     await page.locator('#art').screenshot({path:join(folder,`frame-${String(i).padStart(3,'0')}.png`)});
   }
   // Exercise both transitions across the attachment boundary and reverse seeking.
   const markup=await page.evaluate(()=>{ContactStage.draw(6);return document.querySelector('#art').outerHTML;});
   await page.evaluate(()=>ContactStage.draw(0));
   assert.equal(await page.evaluate(()=>{ContactStage.draw(6);return document.querySelector('#art').outerHTML;}),markup);
   const near=await page.evaluate(()=>{const t=ContactStage.events.attach;return [ContactStage.draw(t-1e-7),ContactStage.draw(t),ContactStage.draw(t+1e-7)];});
   assert(Math.hypot(near[0].rendered.prop.x-near[2].rendered.prop.x,near[0].rendered.prop.y-near[2].rendered.prop.y)<.001);
   const attached=trace.filter(r=>r.state.contact.attached);
   assert(attached.length>0);
   assert.equal(new Set(attached.map(r=>r.rendered.local_attachment)).size,1);
   for(const r of attached){
     assert.equal(r.rendered.parent,scene==='curtain'?'left-object-slot':'right-object-slot');
     assert(r.rendered.prop_before_fingers);
     assert(r.rendered.active_arm_in_front_of_torso);
     assert(Math.hypot(r.rendered.hand.x-r.rendered.prop.x,r.rendered.hand.y-r.rendered.prop.y)<.001);
   }
   const stable=await page.evaluate(()=>document.querySelector('#art').outerHTML);
   await page.evaluate(()=>{try{ContactStage.load('curtain',{...ActorContact.fixtures.curtain,action:'walk'});throw Error('unexpected_acceptance');}catch(e){if(e.message==='unexpected_acceptance')throw e;}});
   assert.equal(await page.locator('#art').evaluate(e=>e.outerHTML),stable);
   writeFileSync(join(folder,'trace.json'),JSON.stringify(trace,null,2));
   const spec=await page.evaluate(()=>({request:ContactStage.request,events:ContactStage.events}));
   const sourceFiles=['contact.js','stage.js','stage.html','output/actor-data.js','../actor-performance/asset-player.js','../actor-performance/performance.js','../layered-motion/performance.js','../../video-generator/hyperframes-runtime/node_modules/gsap/dist/gsap.min.js'];
   const snapshots={};
   for(const [i,p]of sourceFiles.entries()){
     const filename=`source-${i}.txt`;writeFileSync(join(folder,filename),readFileSync(join(dir,p)));snapshots[p]=filename;
   }
   writeFileSync(join(folder,'capture.json'),JSON.stringify({...spec,fps:30,frame_count:times.length,render_errors:errors,
     source_hashes:Object.fromEntries(sourceFiles.map(p=>[p,hash(join(dir,p))])),source_snapshots:snapshots,
     attachment_jump_px:Math.hypot(near[0].rendered.prop.x-near[2].rendered.prop.x,near[0].rendered.prop.y-near[2].rendered.prop.y),
     fixed_local_attachment:true,reverse_seek_exact:true,production_ready:false,human_review:'PENDING',paid_api_calls:0},null,2));
 }
 assert.deepEqual(errors,[]);console.log(JSON.stringify({output:out,video,errors}));
}finally{await browser.close();}
