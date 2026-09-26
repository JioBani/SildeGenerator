import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';
const require=createRequire(new URL('../web/package.json',import.meta.url));
const {chromium}=require('@playwright/test');
const root=path.resolve(process.argv[2]),browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1920,height:1080}});
 await page.goto(pathToFileURL(path.join(root,'index.html')).href);
 const result=await page.evaluate(()=>{
  const tl=window.__timelines['blood-factors-study'],panel=document.getElementById('microPanel');let maxError=0;
  for(const row of window.__microTrack){tl.seek(row.time,true);const m=panel.getCTM();maxError=Math.max(maxError,Math.abs(m.e-row.x),Math.abs(m.f-row.y));}
  tl.seek(19,true);const hold=panel.getCTM();const centered=Math.abs(hold.e)<.01&&Math.abs(hold.f)<.01;
  tl.seek(21.5,true);const exit=panel.getCTM();const downwardExit=Math.abs(exit.e)<.01&&exit.f>0;
  tl.seek(22,true);const final=panel.getCTM();const fullyOffscreen=final.f>=1080;
  panel.setAttribute('transform','translate(-1920 0)');const bad=panel.getCTM();
  return {measuredSamples:window.__microTrack.length,maxError,centered,downwardExit,fullyOffscreen,wrongDirectionDetected:Math.abs(bad.e)>1&&bad.f===0};
 });
 result.pass=result.measuredSamples>30&&result.maxError<.01&&result.centered&&result.downwardExit&&result.fullyOffscreen&&result.wrongDirectionDetected;
 result.scope='Measured panel boundary transform, not particle interaction, audio or full fidelity';
 await fs.writeFile(path.join(root,'micro-review.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));if(!result.pass)process.exitCode=1;
}finally{await browser.close()}
