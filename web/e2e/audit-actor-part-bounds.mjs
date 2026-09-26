import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {dirname,resolve,join} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const dir=join(root,'experiments/actor-performance/output/standard-actor-v3');
const manifest=JSON.parse(readFileSync(join(dir,'manifest.json'),'utf8'));
const browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
try{
 const page=await browser.newPage();await page.setContent('<canvas></canvas>');
 const measure=async svg=>page.evaluate(async text=>{
   const doc=new DOMParser().parseFromString(text,'image/svg+xml'),box=doc.documentElement.getAttribute('viewBox').split(' ').map(Number);
   const width=Math.ceil(box[2]),height=Math.ceil(box[3]),image=new Image();
   image.src='data:image/svg+xml,'+encodeURIComponent(text);await image.decode();
   const canvas=document.querySelector('canvas');canvas.width=width;canvas.height=height;
   const ctx=canvas.getContext('2d');ctx.clearRect(0,0,width,height);ctx.drawImage(image,0,0,width,height);
   const pixels=ctx.getImageData(0,0,width,height).data;let edge=0,total=0;
   for(let y=0;y<height;y++)for(let x=0;x<width;x++)if(pixels[(y*width+x)*4+3]>0){total++;if(x<2||y<2||x>=width-2||y>=height-2)edge++;}
   return {width,height,edge_alpha_pixels:edge,visible_pixels:total};
 },svg);
 const result=[];
 for(const part of manifest.parts){
   const measured=await measure(readFileSync(join(dir,part.path),'utf8'));
   assert(measured.visible_pixels>0,part.id+':blank');assert.equal(measured.edge_alpha_pixels,0,part.id+':clipped');
   assert(part.pivot_in_viewbox.every((p,i)=>p>=0&&p<=part.viewBox[i+2]));
   result.push({id:part.id,...measured});
 }
 const old=await measure(readFileSync(join(dir,'../standard-actor-v2/left-upper.svg'),'utf8'));
 assert(old.edge_alpha_pixels>0,'Negative control must expose old clipped stroke');
 const report={checked_at:new Date().toISOString(),parts:result,old_left_upper_negative_control:old,scope:'Standalone vector file bounds and inherited styles; no design approval',production_ready:false};
 writeFileSync(join(dir,'bounds-audit.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}finally{await browser.close();}
