import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';
const require=createRequire(new URL('../web/package.json',import.meta.url));
const {chromium}=require('@playwright/test');
const root=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
try{await fs.access(out);throw new Error('Preserve previous report')}catch(e){if(e.code!=='ENOENT')throw e}
const meta=JSON.parse(await fs.readFile(path.join(root,'meta.json'),'utf8'));
const program=JSON.parse(await fs.readFile(path.join(root,'scene-program.json'),'utf8'));
const durations=process.argv[4]?JSON.parse(process.argv[4]):[meta.duration];
if(durations.length!==program.scenes.length||durations.some(d=>!Number.isFinite(d)||d<=0)||Math.abs(durations.reduce((a,b)=>a+b,0)-meta.duration)>.00001)throw new Error('Explicit scene durations must match composition');
let offset=0;
const tracks=program.scenes.flatMap((scene,i)=>{
 const items=scene.transport_tracks.map(t=>({...t,sceneIndex:i+1,start:offset,duration:durations[i]}));
 offset+=durations[i];return items;
});
if(!tracks?.length)throw new Error('No transport tracks');
function expected(points,t){
 if(t<=points[0].time)return points[0];
 if(t>=points.at(-1).time)return points.at(-1);
 const j=points.findIndex(p=>p.time>=t),a=points[j-1],b=points[j],u=(t-a.time)/(b.time-a.time);
 return {x:a.x+(b.x-a.x)*u,y:a.y+(b.y-a.y)*u};
}
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage({viewport:meta.resolution});
 await page.goto(pathToFileURL(path.join(root,'index.html')).href);
 await page.waitForFunction(id=>Boolean(window.__timelines?.[id]),meta.name);
 const frames=Math.round(meta.duration*meta.fps),errors=[],forward=[];
 let maxError=0,checks=0;
 async function inspect(frame,reverse){
  const time=frame/meta.fps;
  const actual=await page.evaluate(({time,id})=>{
   window.__timelines[id].seek(time,true);
   return [...document.querySelectorAll('.transport-token')].map(e=>{
    const r=e.getBoundingClientRect();return {id:e.id,x:r.x+r.width/2,y:r.y+r.height/2,label:e.textContent};
   });
  },{time,id:meta.name});
  if(actual.length!==tracks.length)throw new Error('Token count mismatch');
  tracks.forEach(track=>{
   const point=actual.find(p=>p.id===`token-${track.sceneIndex}-${track.id}`);
   if(!point)throw new Error('Missing target');
   const local=Math.max(0,Math.min(track.duration,time-track.start));
   const wanted=expected(track.points,local);
   const events=(track.states||[]).filter(e=>e.time<=local);
   const label=events.length?events.at(-1).label:track.label;
   if(point.label!==label)errors.push({frame,reverse,id:track.id,reason:'state label mismatch',expected:label,actual:point.label});
   const error=Math.max(Math.abs(point.x-wanted.x*meta.resolution.width),Math.abs(point.y-wanted.y*meta.resolution.height));
   maxError=Math.max(maxError,error);checks++;
   if(error>.25)errors.push({frame,reverse,id:track.id,error});
  });
  if(!reverse)forward[frame]=actual;
  else if(JSON.stringify(actual)!==JSON.stringify(forward[frame]))errors.push({frame,reason:'order-dependent'});
 }
 for(let f=0;f<frames;f++)await inspect(f,false);
 for(let f=frames-1;f>=0;f--)await inspect(f,true);
 const report={pass:errors.length===0,frames,checks,maxErrorPixels:maxError,errors,
  scope:'Rendered token centers and labels at every output frame in forward/reverse order, with explicit scene offsets. Includes hidden tokens; no visual occlusion, narration or comprehension approval.'};
 await fs.writeFile(out,JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 if(!report.pass)process.exitCode=1;
}finally{await browser.close()}
