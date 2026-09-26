import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';
const require=createRequire(new URL('../web/package.json',import.meta.url));
const {chromium}=require('@playwright/test');
const root=path.resolve(process.argv[2]),report=path.resolve(process.argv[3]);
try{await fs.access(report);throw new Error('Preserve existing report')}catch(e){if(e.code!=='ENOENT')throw e}
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1920,height:1080}});
 await page.goto(pathToFileURL(path.join(root,'index.html')).href);
 await page.waitForFunction(()=>Boolean(window.__timelines?.['blood-bulge-study']));
 const result=await page.evaluate(()=>{
  const ellipses=[...document.querySelectorAll('[data-cell] ellipse')];
  if(!ellipses.length)throw new Error('Missing ellipse geometry');
  const rx=Number(ellipses[0].getAttribute('rx')),ry=Number(ellipses[0].getAttribute('ry'));
  if(!(rx>0&&ry>0)||ellipses.some(e=>Number(e.getAttribute('rx'))!==rx||Number(e.getAttribute('ry'))!==ry||e.getAttribute('transform')!=='rotate(-40)'))throw new Error('Requires identical aligned ellipses');
  const angle=-40*Math.PI/180,c=Math.cos(angle),s=Math.sin(angle);
  let minNormalizedDistance=Infinity,collisions=0,checkedPairs=0,maxYStep=0,previous;
  for(let f=0;f<209;f++){
   window.__timelines['blood-bulge-study'].seek(f/30,true);
   const points=[...document.querySelectorAll('[data-cell]')].map(node=>{
    const m=node.transform.baseVal.consolidate().matrix;
    return {x:m.e,y:m.f};
   });
   if(points.length!==36)throw new Error('Missing particle');
   if(previous)points.forEach((p,i)=>{maxYStep=Math.max(maxYStep,Math.abs(p.y-previous[i].y))});
   for(let i=0;i<points.length;i++)for(let j=i+1;j<points.length;j++){
    const dx=points[i].x-points[j].x,dy=points[i].y-points[j].y;
    // Equal aligned ellipses overlap iff their transformed center distance is <2.
    const distance=Math.hypot((dx*c+dy*s)/rx,(-dx*s+dy*c)/ry);
    minNormalizedDistance=Math.min(minNormalizedDistance,distance);
    if(distance<2-1e-6)collisions++;
    checkedPairs++;
   }
   previous=points;
  }
  return {frames:209,particles:36,rx,ry,checkedPairs,collisions,minNormalizedDistance,maxYStep,
   pass:collisions===0,scope:'Pairwise equal-ellipse overlap at rendered frame times, including offscreen centers. Not wall clearance, source fidelity, or human motion approval.'};
 });
 await fs.writeFile(report,JSON.stringify(result,null,2));
 console.log(JSON.stringify(result));
 if(!result.pass)process.exitCode=1;
}finally{await browser.close()}
