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
 await page.waitForFunction(()=>Boolean(window.__timelines?.['bird-flu-study']));
 const rows=await page.evaluate(()=>{
  const timeline=window.__timelines['bird-flu-study'];
  const endpoint=id=>{let el=document.querySelector(id);return el.getPointAtLength(el.getTotalLength()).matrixTransform(el.getScreenCTM())};
  const out=[];
  for(let f=426;f<540;f++){
   timeline.seek(f/30,true);
   const left=endpoint('#leftArm'),right=endpoint('#rightArm');
   const hand=document.querySelector('#hands');
   const center=new DOMPoint(960,680).matrixTransform(hand.getScreenCTM());
   out.push({frame:f,gap:Math.hypot(left.x-right.x,left.y-right.y),handGap:Math.hypot(left.x-center.x,left.y-center.y)});
  }
  return out;
 });
 const report={frames:rows.length,maxEndpointGap:Math.max(...rows.map(r=>r.gap)),maxHandGap:Math.max(...rows.map(r=>r.handGap)),scope:'geometric endpoints only; not acting, skin overlap or grasp approval',rows};
 await fs.writeFile(path.join(root,'contact-review.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify({...report,rows:undefined}));
 if(report.maxEndpointGap>.5||report.maxHandGap>.5)process.exitCode=1;
}finally{await browser.close()}
