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
  const tl=window.__timelines['blood-pressure-study'],rows=window.measuredWalls.rows;
  const paths=[...document.querySelector('#walls').children];
  let maxError=0;
  for(const row of rows){
   tl.seek(row.source_second-57,true);
   for(const [side,key]of [[0,'upper'],[1,'lower']]){
    const nums=paths[side*4].getAttribute('d').match(/-?\d+(?:\.\d+)?/g).map(Number);
    for(let i=0;i<row[key].length;i++){
     const [x,y]=row[key][i];
     maxError=Math.max(maxError,Math.abs(nums[(i+1)*2]-x*3),Math.abs(nums[(i+1)*2+1]-y*3));
    }
   }
  }
  return {sampledSourceFrames:rows.length,maxControlPointErrorPixels:maxError,sourceSha256:window.measuredWalls.source_sha256};
 });
 result.scope='Native PTS curve control points only, not rendered silhouette, typography, anatomy or visual approval';
 result.pass=result.sampledSourceFrames>300&&result.maxControlPointErrorPixels<.01;
 await fs.writeFile(path.join(root,'curve-review.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify(result));if(!result.pass)process.exitCode=1;
}finally{await browser.close()}
