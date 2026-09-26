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
 const evidence=await page.evaluate(()=>{
  const tl=window.__timelines['blood-flow-study'];
  const particles=[...document.querySelector('#particles').children];
  let previous,minForwardDelta=Infinity,steps=0;
  for(let frame=189;frame<=266;frame++){
   tl.seek(frame/30,true);
   const now=particles.map(e=>new DOMPoint(0,0).matrixTransform(e.getCTM()).x);
   if(previous){minForwardDelta=Math.min(minForwardDelta,...now.map((x,i)=>x-previous[i]));steps++}
   previous=now;
  }
  const states=[];
  for(const [time,label] of [[1.5,'oxygen'],[6.5,'flow'],[10,'pressure'],[21,'systole'],[28,'systolic_pressure']]){
   tl.seek(time,true);
   states.push({time,label,gallery:Number(getComputedStyle(document.querySelector('#gallery')).opacity),vessel:Number(getComputedStyle(document.querySelector('#vessel')).opacity),particles:Number(getComputedStyle(document.querySelector('#particles')).opacity),pressure:Number(getComputedStyle(document.querySelector('#pressure')).opacity),caption:document.querySelector('#pressureLabel').textContent});
  }
  return {minForwardDelta,steps,particles:particles.length,states};
 });
 const s=evidence.states;
 const pass=evidence.minForwardDelta>0&&s[0].gallery===1&&s[1].gallery===0&&s[1].vessel===1&&s[2].particles===0&&s[2].pressure===1&&s[3].caption==='SYSTOLE'&&s[4].caption==='SYSTOLIC PRESSURE';
 const report={pass,scope:'Visible flow direction and selected scene states only; not physiology or source fidelity',...evidence};
 await fs.writeFile(path.join(root,'flow-review.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify(report));if(!pass)process.exitCode=1;
}finally{await browser.close()}
