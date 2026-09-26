import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {existsSync,mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import {dirname,join,resolve} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..'),dir=join(root,'experiments/actor-d-upper-body');
const video=process.argv.includes('--video');
const version=process.argv.find(a=>a.startsWith('--version='))?.slice(10)||'v1';
assert.match(version,/^v[1-9][0-9]*$/);
const out=join(dir,'output',video?version:'inspection-'+version);
assert(!existsSync(out),'Existing capture is preserved; use a new version');mkdirSync(out);
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
try{
 const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1}),errors=[];
 page.setDefaultTimeout(30000);page.on('pageerror',e=>{errors.push(e.message);console.error(e.message);});await page.route(/^https?:/,r=>r.abort());
 await page.goto(pathToFileURL(join(dir,'stage.html')).href);await page.waitForFunction(()=>!!window.DUpperStage);
 await page.evaluate(()=>Promise.all([...document.images].map(i=>i.decode())));
 const original=await browser.newPage({viewport:{width:1920,height:1080}});
 await original.goto(pathToFileURL(join(root,'experiments/light-pollution-story-asset-v1/D/project/index.html')).href);
 const faceState=()=>{
   const values={};for(const sel of ['.head','.notice','.squint','.face-light','.collar-front']){
     const s=getComputedStyle(document.querySelector(sel));values[sel]=[s.opacity,s.transform,s.transformOrigin,s.filter,sel==='.collar-front'?'narrowed_to_neckline':s.clipPath,s.width,s.height];
   }return values;
 };
 const comparedTimes=[0,1.5,1.9,2.35,2.9,3.4,4.8,5.1,6,9.4];
 for(const time of comparedTimes){
   await original.evaluate(t=>{window.__timelines['story-d'].time(t,false);},time);
   await page.evaluate(t=>DUpperStage.draw(t),time);
   assert.deepEqual(await page.evaluate(faceState),await original.evaluate(faceState),'source face/neckline timing:'+time);
 }
 const distance=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
 for(const name of ['lower','higher']){
   const folder=join(out,name);mkdirSync(folder);
   const fixture=await page.evaluate(n=>DUpperBody.fixtures[n],name);
   await page.evaluate(r=>DUpperStage.load(r),fixture);
   const times=video?Array.from({length:300},(_,i)=>i/30):[0,1.9,2.9,4,5.5,6.5,7.5,9.9];
   const trace=[];
   for(let i=0;i<times.length;i++){
     trace.push(await page.evaluate(t=>DUpperStage.draw(t),times[i]));
     await page.locator('#stage').screenshot({path:join(folder,`frame-${String(i).padStart(3,'0')}.png`)});
   }
   for(const t of trace){
     assert(distance(t.rendered.upper_end,t.rendered.elbow)<.001);
     assert(distance(t.rendered.forearm_end,t.rendered.wrist)<.001);
     assert(Math.abs(distance(t.rendered.shoulder,t.rendered.elbow)-237.8)<.001);
     assert(Math.abs(distance(t.rendered.elbow,t.rendered.wrist)-Math.hypot(2.5,206.25))<.001);
   }
   const targetError=distance(trace.at(-1).rendered.palm,fixture.target);assert(targetError<.001);
   const markup=await page.locator('#stage').evaluate(e=>e.outerHTML);
   const final=await page.screenshot({path:join(folder,'reverse-before.png')});await page.evaluate(()=>DUpperStage.draw(0));await page.evaluate(t=>DUpperStage.draw(t),times.at(-1));
   const reverse=await page.screenshot({path:join(folder,'reverse-after.png')});
   const reverseMarkup=markup===await page.locator('#stage').evaluate(e=>e.outerHTML);
   const reversePixels=final.equals(reverse);
   writeFileSync(join(folder,'trace.json'),JSON.stringify(trace));
   const sources=['stage.html','stage.js','performance.js','output/actor-data.js','../actor-binding/rig.js','../light-pollution-story-asset-v1/D/project/assets/gsap.min.js'];
   const snapshots={};
   for(const[i,file]of sources.entries()){const saved=`source-${i}.txt`;writeFileSync(join(folder,saved),readFileSync(join(dir,file)));snapshots[file]={file:saved,sha256:hash(join(dir,file))};}
   writeFileSync(join(folder,'capture.json'),JSON.stringify({fixture,snapshots,fps:30,frame_count:times.length,target_error_px:targetError,
     rendered_bone_lengths_fixed:true,rendered_joint_endpoints_match:true,source_face_timing_samples:comparedTimes,
     source_assembly_properties_equal_except_collar_clip:true,reverse_pixels_exact:reversePixels,reverse_markup_exact:reverseMarkup,render_errors:errors,
     trace_sha256:hash(join(folder,'trace.json')),human_review:'PENDING_NEW_ASSEMBLY',production_ready:false,
     frame_hashes:times.map((_,i)=>hash(join(folder,`frame-${String(i).padStart(3,'0')}.png`))),
     builtin_image_generation_calls:1,paid_api_calls:0},null,2));
   console.log(JSON.stringify({scene:name,target_error_px:targetError,frames:times.length}));
 }
 assert.deepEqual(errors,[]);
}finally{await browser.close();}
