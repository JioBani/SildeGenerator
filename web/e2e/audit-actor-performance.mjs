import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import {dirname,resolve,join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const contact=process.argv.includes('--contact'),scenes=contact?['retain','curtain']:['result','glare'],duration=contact?8:6;
const version=contact?'v2':'v1';
const dir=join(root,'experiments',contact?'actor-contact':'actor-performance'),out=join(dir,'output/browser-audit');
mkdirSync(out,{recursive:true});
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
const browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
const checks=[];
try{
 const page=await browser.newPage({viewport:{width:1360,height:1050},acceptDownloads:true});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(join(dir,'review.html')).href);
 await page.waitForFunction(()=>[...document.querySelectorAll('video')].every(v=>v.readyState>=2));
 const metadata=await page.locator('video').evaluateAll(vs=>vs.map(v=>({width:v.videoWidth,height:v.videoHeight,duration:v.duration,error:v.error?.message})));
 for(const m of metadata){assert.equal(m.width,1000);assert.equal(m.height,820);assert.equal(m.duration,duration);assert.equal(m.error,undefined);}
 checks.push(`two videos decoded: 1000x820, ${duration} seconds`);
 for(const scene of scenes){
   const receipt=JSON.parse(readFileSync(join(dir,'output',version,scene,'receipt.json'),'utf8'));
   assert.equal(receipt.video_sha256,hash(join(dir,'output',version,scene,'motion.mp4')));
   for(const [p,h] of Object.entries(receipt.source_hashes))assert.equal(hash(join(dir,p)),h);
   assert.equal(receipt.production_ready,false);
 }
 checks.push('video and source hashes match receipts; no production approval');
 await page.locator('#play').click();
 await page.waitForFunction(()=>[...document.querySelectorAll('video')].every(v=>v.currentTime>1));
 await page.locator('#pause').click();
 assert.ok(await page.locator('video').evaluateAll(vs=>vs.every(v=>v.paused)));
 checks.push('both videos play and pause');
 await page.locator('#reset').click();
 assert.ok(await page.locator('video').evaluateAll(vs=>vs.every(v=>v.paused&&v.currentTime===0)));
 checks.push('reset restores both videos');
 await page.locator('#save').click();
 assert.match(await page.locator('#message').textContent(),/작성/);
 checks.push('empty review cannot export');
 for(const id of ['meaning-a','meaning-b'])await page.locator('#'+id).fill('AUTOMATED TEST ONLY - NOT HUMAN FEEDBACK');
 for(const id of ['motion-a','motion-b'])await page.locator('#'+id).selectOption('unclear');
 const downloaded=page.waitForEvent('download');await page.locator('#save').click();
 const download=await downloaded,record=JSON.parse(readFileSync(await download.path(),'utf8'));
 assert.equal(record.production_ready,false);
 assert.equal(record.status,'OBSERVATION_REQUIRES_IMPORT_AND_VERIFICATION');
 for(const scene of scenes)assert.equal(record.evidence[scene].video_sha256,hash(join(dir,'output',version,scene,'motion.mp4')));
 checks.push('synthetic download binds exact videos, grants no approval');
 // Never import synthetic feedback into the human review ledger.
 for(const id of ['meaning-a','meaning-b'])await page.locator('#'+id).fill('');
 for(const id of ['motion-a','motion-b'])await page.locator('#'+id).selectOption('');
 await page.evaluate(()=>document.querySelector('#message').textContent='');
 await page.locator('video').evaluateAll(async vs=>{await Promise.all(vs.map(v=>new Promise(resolve=>{v.addEventListener('seeked',resolve,{once:true});v.currentTime=3.5;})));});
 await page.screenshot({path:join(out,'desktop.png'),fullPage:true});
 await page.setViewportSize({width:390,height:844});
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 const boxes=await page.locator('video').evaluateAll(vs=>vs.map(v=>{const b=v.getBoundingClientRect();return {left:b.left,right:b.right,top:b.top,bottom:b.bottom};}));
 assert.ok(boxes.every(b=>b.left>=0&&b.right<=390));assert.ok(boxes[1].top>boxes[0].bottom);
 await page.screenshot({path:join(out,'mobile.png'),fullPage:true});
 checks.push('390px mobile videos fit and stack without overlap');
 assert.deepEqual(errors,[]);checks.push('no page errors');
 const result={checked_at:new Date().toISOString(),checks,metadata,review_html_sha256:hash(join(dir,'review.html')),human_review:'PENDING',production_ready:false};
 writeFileSync(join(out,'audit.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}finally{await browser.close();}
