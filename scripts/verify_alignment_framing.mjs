import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';
const require=createRequire(new URL('../web/package.json',import.meta.url));
const {chromium}=require('@playwright/test');
const root=path.resolve(process.argv[2]);
const browser=await chromium.launch({channel:'chrome',headless:true});
try {
 const page=await browser.newPage({viewport:{width:1920,height:1080}});
 await page.goto(pathToFileURL(path.join(root,'index.html')).href);
 await page.waitForFunction(()=>Boolean(window.__timelines?.['posture-alignment-study']));
 async function inspect(t,negative=false){return page.evaluate(({t,negative})=>{
  window.__timelines['posture-alignment-study'].seek(t,true);
  const head=document.querySelector('#performanceHead');
  const saved=head.getAttribute('transform');
  if(negative)head.setAttribute('transform','translate(240 175) rotate(85)');
  const stage=document.querySelector('svg').getBoundingClientRect();
  const bounds=id=>{const r=document.querySelector(id).getBoundingClientRect();return {
   left:(r.left-stage.left)/3,right:(r.right-stage.left)/3,
   top:(r.top-stage.top)/3,bottom:(r.bottom-stage.top)/3};};
  const h=bounds('#performanceHead'),g=bounds('#performanceGrip');
  const opacity=Number(getComputedStyle(document.querySelector('#profilePerformance')).opacity);
  const pass=opacity>0&&h.left>=0&&h.right<=640&&g.left>=0&&g.right<=640&&g.top>=0&&g.bottom<=360;
  if(negative)head.setAttribute('transform',saved);
  return {time:t,head:h,grip:g,opacity,pass};
 },{t,negative});}
 const rows=[];
 // Entry is an intentional off-screen move; the top of the upright headpiece is also cropped in source.
 for(let frame=223;frame<=241;frame++)rows.push(await inspect(frame/30));
 const negative=await inspect(7.5,true);
 const pass=rows.every(r=>r.pass)&&!negative.pass;
 await fs.writeFile(path.join(root,'framing-review.json'),JSON.stringify({pass,rows,negative,
  limitations:'Horizontal head and full grip bounds after entry only. Not source pose fidelity, neck contact, silhouette identity, anatomical validation or perceptual quality approval.'},null,2));
 console.log(JSON.stringify({pass,frames:rows.length,failures:rows.filter(r=>!r.pass),negativeRejected:!negative.pass}));
 if(!pass)process.exitCode=1;
}finally{await browser.close();}
