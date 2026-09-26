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
  const $=id=>document.getElementById(id),tl=window.__timelines['blood-pressure-study'];
  const opacity=e=>Number(getComputedStyle(e).opacity);
  const rows=[];let previousWave,changed=0;
  for(let frame=0;frame<900;frame++){
   tl.seek(frame/30,true);
   const labels=[...$('labels').children].filter(e=>opacity(e)>.01);
   const seam=$('bodyPanel').getCTM().e-($('field').getCTM().e+1920);
   const wave=$('walls').firstElementChild.getAttribute('d');
   if(previousWave!==undefined&&wave!==previousWave)changed++;
   previousWave=wave;
   const matrix=$('heart').getCTM();
   rows.push({frame,labels:labels.map(e=>e.id),seam,heartScale:Math.hypot(matrix.a,matrix.b)});
  }
  const expected=[[4.5,'diastolicA'],[8.5,'systolic'],[11,'rangeHigh'],[14.5,'diastolicB'],[17,'rangeLow'],[20.5,'combined']];
  const states=expected.map(([time,id])=>({time,id,pass:rows[Math.round(time*30)].labels.join(',')===id}));
  tl.seek(25,true);const title=$('bodyTitle').getBoundingClientRect();
  const finalBodyVisible=Math.abs($('bodyPanel').getCTM().e)<.01&&opacity($('bodyTitle'))>.99;
  const titleInside=title.left>=0&&title.right<=1920&&title.top>=0&&title.bottom<=1080;
  tl.seek(11,true);$('diastolicB').style.opacity='1';
  const mutationDetected=[...$('labels').children].filter(e=>opacity(e)>.01).length>1;
  return {frames:900,minHeartScale:Math.min(...rows.filter(r=>r.frame<150).map(r=>r.heartScale)),maxConcurrentLabels:Math.max(...rows.map(r=>r.labels.length)),maxTransitionSeam:Math.max(...rows.map(r=>Math.abs(r.seam))),changedWaveFrames:changed,states,finalBodyVisible,titleInside,mutationDetected};
 });
 result.scope='Label sequencing, transition coverage and visible final diagram; not physiology, waveform or source-fidelity approval';
 result.pass=result.minHeartScale>=.939&&result.maxConcurrentLabels===1&&result.maxTransitionSeam<.01&&result.changedWaveFrames>800&&result.states.every(r=>r.pass)&&result.finalBodyVisible&&result.titleInside&&result.mutationDetected;
 await fs.writeFile(path.join(root,'pressure-review.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify(result));if(!result.pass)process.exitCode=1;
}finally{await browser.close()}
