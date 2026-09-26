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
  const timeline=window.__timelines['posture-bend-study'];
  function endpoint(id){const e=document.getElementById(id);return e.getPointAtLength(e.getTotalLength()).matrixTransform(e.getCTM())}
  function origin(id){return new DOMPoint(0,0).matrixTransform(document.getElementById(id).getCTM())}
  function distance(a,b){return Math.hypot(a.x-b.x,a.y-b.y)}
  const rows=[];
  let feetBaseline;
  for(let frame=0;frame<360;frame++){
   timeline.seek(frame/30,true);
   const inverse=document.getElementById('actor').getCTM().inverse();
   const feet=['frontLeg','backLeg'].map(id=>endpoint(id).matrixTransform(inverse));
   feetBaseline??=feet;
   rows.push({frame,handGap:distance(endpoint('nearArm'),origin('hand')),
    neckGap:distance(endpoint('neck'),origin('head')),
    footDrift:Math.max(...feet.map((p,i)=>distance(p,feetBaseline[i])))});
  }
  // Mutation proves that this check detects a detached hand instead of only reading declarations.
  document.getElementById('hand').setAttribute('transform','translate(1500 812) rotate(76)');
  const mutationGap=distance(endpoint('nearArm'),origin('hand'));
  return {rows,mutationGap};
 });
 const report={scope:'Geometry only, not source fidelity, weight shift or acting approval',
  frames:result.rows.length,maxHandGap:Math.max(...result.rows.map(r=>r.handGap)),
  maxNeckGap:Math.max(...result.rows.map(r=>r.neckGap)),
  maxFootDrift:Math.max(...result.rows.map(r=>r.footDrift)),
  detachedHandDetected:result.mutationGap>100,rows:result.rows};
 report.pass=report.maxHandGap<.1&&report.maxNeckGap<.1&&report.maxFootDrift<.1&&report.detachedHandDetected;
 await fs.writeFile(path.join(root,'geometry-review.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify({...report,rows:undefined}));
 if(!report.pass)process.exitCode=1;
}finally{await browser.close()}
