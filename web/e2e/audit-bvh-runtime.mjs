import {chromium} from '@playwright/test';
import {mkdirSync,writeFileSync} from 'node:fs';
import {dirname,resolve,join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const dir=join(root,'experiments/actor-motion-runtime');
const output=join(dir,'output/browser-audit');
mkdirSync(output,{recursive:true});
const browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
const results=[];
const check=(name,pass)=>{results.push({name,pass});if(!pass)throw new Error(name);};
try{
  const page=await browser.newPage({viewport:{width:1280,height:1000}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(pathToFileURL(join(dir,'review.html')).href);
  await page.waitForFunction(()=>[...document.querySelectorAll('video')].every(v=>v.readyState>=2));
  check('two_720p_six_second_videos',await page.evaluate(()=>[...document.querySelectorAll('video')].every(v=>v.videoWidth===720&&v.videoHeight===720&&Math.abs(v.duration-6)<.05)));
  await page.locator('#play').click();
  await page.waitForFunction(()=>[...document.querySelectorAll('video')].every(v=>v.currentTime>1));
  check('both_playing',await page.evaluate(()=>[...document.querySelectorAll('video')].every(v=>!v.paused)));
  await page.locator('#pause').click();
  check('both_paused',await page.evaluate(()=>[...document.querySelectorAll('video')].every(v=>v.paused)));
  await page.evaluate(async()=>{await Promise.all([...document.querySelectorAll('video')].map(v=>new Promise(resolve=>{v.addEventListener('seeked',resolve,{once:true});v.currentTime=4.5})));});
  await page.screenshot({path:join(output,'desktop.png'),fullPage:true});
  await page.locator('#reset').click();
  check('both_reset',await page.evaluate(()=>[...document.querySelectorAll('video')].every(v=>v.currentTime<.05)));
  await page.setViewportSize({width:390,height:844});
  check('mobile_no_overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:join(output,'mobile.png'),fullPage:true});
  const slow=await browser.newPage();
  await slow.goto(pathToFileURL(join(dir,'output/astra-wave-slow-v1/motion.mp4')).href);
  await slow.waitForFunction(()=>document.querySelector('video')?.readyState>=2);
  check('slow_variant_decodes',await slow.evaluate(()=>Math.abs(document.querySelector('video').duration-6)<.05));
  check('no_page_errors',errors.length===0);
}finally{
  writeFileSync(join(output,'results.json'),JSON.stringify(results,null,2));
  await browser.close();
}
console.log(JSON.stringify(results));
