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
 await page.waitForFunction(()=>Boolean(window.__timelines?.['posture-alignment-study']));
 const result=await page.evaluate(()=>{
  const rows=[];
  for(const row of window.alignmentEvidence.rows){
   if(row.source_second<112||row.source_second>114)continue;
   const points=row.divider_x===null?row.points:row.left;
   if(points.length<20)continue;
   const xs=points.map(p=>p.x).sort((a,b)=>a-b);
   if(xs.at(-1)-xs[0]>8)continue;
   window.__timelines['posture-alignment-study'].seek(row.source_second-106,true);
   const front=document.querySelector('#front');
   const actual=front.transform.baseVal.consolidate().matrix.e;
   const expected=xs[Math.floor(xs.length/2)];
   const divider=Number(document.querySelector('#sideField').getAttribute('x'));
   const performer=document.querySelector('#profilePerformance');
   const opacity=Number(getComputedStyle(performer).opacity);
   const actorX=performer.transform.baseVal.consolidate().matrix.e;
   const reveal=document.querySelector('#profileRevealRect');
   const entryPass=row.source_second>=113.7||
    (row.divider_x===null?opacity===0:opacity>0&&Math.abs(actorX-440)<.05&&
     reveal!==null&&Math.abs(Number(reveal.getAttribute('x'))-divider)<.05);
   const actorError=Math.abs(actual-expected);
   const dividerError=row.divider_x===null?null:Math.abs(divider-row.divider_x);
   rows.push({source_second:row.source_second,actorError,dividerError,entryPass,
    pass:actorError<.05&&(dividerError===null||dividerError<.05)&&entryPass});
  }
  return {pass:rows.length>30&&rows.every(r=>r.pass),rows,
   limitations:'Coordinate agreement with scene-specific detector, not independent source pose or perceptual approval.'};
 });
 await fs.writeFile(path.join(root,'track-review.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify({pass:result.pass,frames:result.rows.length,failures:result.rows.filter(r=>!r.pass)}));
 if(!result.pass)process.exitCode=1;
}finally{await browser.close()}
