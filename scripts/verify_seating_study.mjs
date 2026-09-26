import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';
const require=createRequire(new URL('../web/package.json',import.meta.url));
const {chromium}=require('@playwright/test');
const root=path.resolve(process.argv[2]);
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1920,height:1080}});
 await page.goto(pathToFileURL(path.join(root,'index.html')).href);
 const result=await page.evaluate(()=>{
  const $=id=>document.getElementById(id),tl=window.__timelines['posture-seating-study'];
  const point=(id,x=0,y=0)=>new DOMPoint(x,y).matrixTransform($(id).getCTM());
  const end=id=>{const p=$(id).getPointAtLength($(id).getTotalLength());return point(id,p.x,p.y)};
  const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
  const errors=[],footWorld=[];
  for(let frame=0;frame<900;frame++){
   tl.seek(frame/30,true);
   errors.push(Math.max(dist(end('nearArm'),point('hand')),dist(end('nearLeg'),point('nearFoot')),dist(end('farLeg'),point('farFoot'))));
   if(frame>=246)footWorld.push(point('nearFoot').matrixTransform($('camera').getCTM().inverse()));
  }
  tl.seek(20,true);
  const gazeStart=$('gaze').getPointAtLength(0),gazeEnd=$('gaze').getPointAtLength($('gaze').getTotalLength());
  const gazeError=dist(point('gaze',gazeStart.x,gazeStart.y),point('head',39,-29));
  const targetError=dist(point('gaze',gazeEnd.x,gazeEnd.y),point('desk',1280,310));
  tl.seek(26,true);
  const handPoint=point('hand',7,4),hit=document.elementFromPoint(handPoint.x,handPoint.y);
  const handVisible=Boolean(hit?.closest('#hand'));
  $('hand').setAttribute('transform','translate(0 0)');
  return {maxEndpointGap:Math.max(...errors),fixedFootDrift:Math.max(...footWorld.map(p=>dist(p,footWorld[0]))),
   gazeError,targetError,handVisible,mutationDetected:dist(end('nearArm'),point('hand'))>100,frames:900};
 });
 result.scope='Endpoint attachment, settled foot stability, gaze target and selected hand visibility only; not anatomy or acting approval';
 result.pass=result.maxEndpointGap<.01&&result.fixedFootDrift<.01&&result.gazeError<.01&&result.targetError<.01&&result.handVisible&&result.mutationDetected;
 await fs.writeFile(path.join(root,'seating-review.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify(result));if(!result.pass)process.exitCode=1;
}finally{await browser.close()}
