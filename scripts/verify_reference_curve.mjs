import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';
const require=createRequire(new URL('../web/package.json',import.meta.url));
const {chromium}=require('@playwright/test');
const root=path.resolve(process.argv[2]);
const measured=JSON.parse(await fs.readFile(process.argv[3],'utf8'));
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1920,height:1080}});
 await page.goto(pathToFileURL(path.join(root,'index.html')).href);
 const rows=await page.evaluate(rows=>rows.map(r=>{
  window.__timelines['blood-intervention-study'].seek(r.source_second-201,true);
  const height=Number(document.getElementById('balloonShape').getAttribute('ry'))*2/3;
  return {source_second:r.source_second,source_height:r.red_height_px,candidate_height:height,error:Math.abs(height-r.red_height_px)};
 }),measured.rows);
 const result={scope:'Central-strip source height versus SVG radius at original PTS; not full visual fidelity',
  source_sha256:measured.source_sha256,count:rows.length,max_error_analysis_pixels:Math.max(...rows.map(r=>r.error)),rows};
 result.pass=result.max_error_analysis_pixels<1;
 await fs.writeFile(path.join(root,'measured-curve-review.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify({count:result.count,max_error:result.max_error_analysis_pixels,pass:result.pass}));
 if(!result.pass)process.exitCode=1;
}finally{await browser.close()}
