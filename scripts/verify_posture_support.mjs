import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';
const require=createRequire(new URL('../web/package.json',import.meta.url));
const {chromium}=require('@playwright/test'),root=path.resolve(process.argv[2]);
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1920,height:1080}});
 await page.goto(pathToFileURL(path.join(root,'index.html')).href);
 await page.waitForFunction(()=>Boolean(window.__timelines?.['posture-consequences-study']));
 async function inspect(t){return page.evaluate(t=>{
  window.__timelines['posture-consequences-study'].seek(t,true);
  const camera=document.querySelector('#hospitalCam'),inv=camera.getCTM().inverse();
  function endpoint(id,end=true){const n=document.getElementById(id),p=n.getPointAtLength(end?n.getTotalLength():0);return new DOMPoint(p.x,p.y).matrixTransform(n.getCTM()).matrixTransform(inv)}
  const wrist=endpoint('restingArm'),foot=endpoint('patientFeet'),leg=endpoint('patientLegs'),arm=document.querySelector('#restingArm');
  const coords=arm.getAttribute('d').match(/-?\d*\.?\d+(?:e[+-]?\d+)?/gi).map(Number);
  const lengths=[Math.hypot(coords[2]-coords[0],coords[3]-coords[1]),Math.hypot(coords[4]-coords[2],coords[5]-coords[3])];
  const errors={wrist:Math.hypot(wrist.x-317,wrist.y-245),foot:Math.hypot(foot.x-551,foot.y-217),leg:Math.hypot(leg.x-490,leg.y-236),upperLength:Math.abs(lengths[0]-95),lowerLength:Math.abs(lengths[1]-115)};
  return {time:t,errors,pass:Object.values(errors).every(e=>Number.isFinite(e)&&e<.01)};
 },t)}
 const rows=[];for(let f=81;f<276;f++)rows.push(await inspect(f/30));
 await page.$eval('#patientFeet',n=>n.setAttribute('transform','translate(12 0)'));
 const negative=await inspect(7.5);
 await page.$eval('#patientFeet',n=>n.removeAttribute('transform'));
 const pass=rows.every(r=>r.pass)&&!negative.pass;
 await fs.writeFile(path.join(root,'support-review.json'),JSON.stringify({pass,rows,negative_control:negative,
  limitations:'Authored bed-space contact and segment invariants only. Does not certify source pose, body anatomy, rendered occlusion or human acting quality.'},null,2));
 console.log(JSON.stringify({pass,frames:rows.length,failures:rows.filter(r=>!r.pass).slice(0,3),negativeRejected:!negative.pass}));
 if(!pass)process.exitCode=1;
}finally{await browser.close()}
