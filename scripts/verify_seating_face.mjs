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
  const tl=window.__timelines['posture-seating-study'];
  const lid=document.getElementById('performanceLid'),mouth=document.getElementById('performanceMouth');
  const states=[];let previous,maxLidStep=0;
  for(let f=0;f<900;f++){
   tl.seek(f/30,true);const h=Number(lid.getAttribute('height'));
   if(previous!==undefined)maxLidStep=Math.max(maxLidStep,Math.abs(h-previous));previous=h;
  }
  for(const [time,expected]of [[0,'tired'],[1,'engaged'],[12,'tired'],[17.5,'tired'],[19,'engaged']]){
   tl.seek(time,true);const h=Number(lid.getAttribute('height')),d=mouth.getAttribute('d');
   const tired=h===25&&d==='M12 19Q31 17 52 19';
   const engaged=h===0&&d==='M12 16Q31 30 52 15';
   states.push({time,expected,height:h,mouth:d,pass:expected==='tired'?tired:engaged});
  }
  tl.seek(18.2,true);const eyeStarted=Number(lid.getAttribute('height'))<25;
  const mouthStillNeutral=mouth.getAttribute('d')==='M12 19Q31 17 52 19';
  return {frames:900,states,maxLidStep,eyeStartedBeforeMouth:eyeStarted&&mouthStillNeutral};
 });
 result.pass=result.states.every(s=>s.pass)&&result.maxLidStep<7&&result.eyeStartedBeforeMouth;
 result.scope='Fixture state presence and transition bounds, not emotion comprehension or source fidelity';
 await fs.writeFile(path.join(root,'face-review.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify(result));if(!result.pass)process.exitCode=1;
 await page.evaluate(()=>{window.__timelines['posture-seating-study'].seek(17.5,true)});
 await page.screenshot({path:path.join(root,'face-tired.png')});
 await page.evaluate(()=>{window.__timelines['posture-seating-study'].seek(19,true)});
 await page.screenshot({path:path.join(root,'face-engaged.png')});
}finally{await browser.close()}
