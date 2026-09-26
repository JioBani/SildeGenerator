import {createRequire} from 'node:module';import {pathToFileURL} from 'node:url';import path from 'node:path';import fs from 'node:fs/promises';
const require=createRequire(new URL('../web/package.json',import.meta.url)),{chromium}=require('@playwright/test');
const root=path.resolve(process.argv[2]),browser=await chromium.launch({channel:'chrome',headless:true});
try{const page=await browser.newPage({viewport:{width:1920,height:1080}});await page.goto(pathToFileURL(path.join(root,'index.html')).href);
 const result=await page.evaluate(()=>{
  const tl=window.__timelines['posture-rest-study'],$=id=>document.getElementById(id);let maxAnkleGap=0;
  for(let f=0;f<120;f++){tl.seek(f/30,true);const leg=$('restFarLeg'),ankle=$('farAnkle'),a=leg.getPointAtLength(leg.getTotalLength()),b=ankle.getPointAtLength(0);maxAnkleGap=Math.max(maxAnkleGap,Math.hypot(a.x-b.x,a.y-b.y));}
  tl.seek(7.5,true);const heel=$('heel').getBoundingClientRect(),shoe=$('trainer').getBoundingClientRect();const separated=shoe.left>heel.right&&shoe.right<1920;
  $('trainer').setAttribute('transform','translate(0 0)');const bad=$('trainer').getBoundingClientRect();const mutationDetected=bad.left<heel.right;
  return {maxAnkleGap,separated,mutationDetected,faceLayerPresent:Boolean(document.querySelector('#scanner use[href="#face"]'))};
 });result.pass=result.maxAnkleGap<.01&&result.separated&&result.mutationDetected&&result.faceLayerPresent;result.scope='Ankle endpoint, comparison separation and face-layer presence only; not contact, anatomy or visual approval';
 await fs.writeFile(path.join(root,'rest-review.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));if(!result.pass)process.exitCode=1;
}finally{await browser.close()}
