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
  const tl=window.__timelines['blood-factors-study'],$=id=>document.getElementById(id);
  const point=(e,x,y)=>new DOMPoint(x,y).matrixTransform(e.getCTM());
  let titleClippedFrames=0,maxLaunchGap=0,hiddenBeforeLaunch=true,downward=true;
  for(let f=0;f<180;f++){
   tl.seek(f/30,true);const r=$('bodyTitle').getBoundingClientRect();
   if(r.top<0||r.left<0||r.right>1920||r.bottom>1080)titleClippedFrames++;
  }
  for(const flight of window.__grainFlights){
   const grain=$(flight.id);
   tl.seek(flight.start-.001,true);hiddenBeforeLaunch&&=Number(getComputedStyle(grain).opacity)===0;
   tl.seek(flight.start,true);
   const a=point(grain,0,0),b=point($('shaker'),flight.holeX,flight.holeY);
   maxLaunchGap=Math.max(maxLaunchGap,Math.hypot(a.x-b.x,a.y-b.y));
   let previous=a.y;
   for(let n=1;n<=21;n++){
    tl.seek(flight.start+(flight.end-flight.start)*n/21,true);
    const y=point(grain,0,0).y;downward&&=y>=previous-.01;previous=y;
   }
  }
  tl.seek(5.9,true);$('bodyPanel').setAttribute('transform','translate(0 -200)');
  const titleMutationDetected=$('bodyTitle').getBoundingClientRect().top<0;
  const first=window.__grainFlights[0];tl.seek(first.start,true);
  $(first.id).setAttribute('transform','translate(0 0)');
  const bad=point($(first.id),0,0),hole=point($('shaker'),first.holeX,first.holeY);
  const launchMutationDetected=Math.hypot(bad.x-hole.x,bad.y-hole.y)>100;
  return {grainCount:window.__grainFlights.length,titleClippedFrames,maxLaunchGap,hiddenBeforeLaunch,downward,titleMutationDetected,launchMutationDetected};
 });
 result.pass=result.grainCount===16&&result.titleClippedFrames===0&&result.maxLaunchGap<.01&&result.hiddenBeforeLaunch&&result.downward&&result.titleMutationDetected&&result.launchMutationDetected;
 result.scope='Title bounds and shaker-to-grain launch only; not source trajectory, tongue contact or natural motion approval';
 await fs.writeFile(path.join(root,'emission-review.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify(result));if(!result.pass)process.exitCode=1;
}finally{await browser.close()}
