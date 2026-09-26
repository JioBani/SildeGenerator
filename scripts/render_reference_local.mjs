// Experimental local seek renderer, used only when the container service is unavailable.
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
const require=createRequire(new URL('../web/package.json',import.meta.url));
const {chromium}=require('@playwright/test');
const root=path.resolve(process.argv[2]),output=path.resolve(process.argv[3]);
const meta=require(path.join(root,'meta.json'));
const browser=await chromium.launch({channel:'chrome',headless:true});
let encoder;
try{
 const page=await browser.newPage({viewport:meta.resolution});
 let pageFailure;
 const failed=new Promise((_,reject)=>{
  page.on('pageerror',error=>{pageFailure=error;reject(new Error(`Scene initialization failed: ${error.message}`))});
 });
 // Attach a rejection handler before navigation can trigger an early script error.
 failed.catch(()=>{});
 await page.goto(pathToFileURL(path.join(root,'index.html')).href);
 await Promise.race([page.waitForFunction(id=>Boolean(window.__timelines?.[id]),meta.name),failed]);
 await page.evaluate(async()=>{
  const sources=[...document.querySelectorAll('img,image')].map(e=>e.getAttribute('src')||e.getAttribute('href')).filter(Boolean);
  await Promise.all([...new Set(sources)].map(async src=>{const im=new Image();im.src=src;await im.decode()}));
  await document.fonts.ready;
 });
 encoder=spawn('ffmpeg',['-y','-v','error','-f','image2pipe','-vcodec','png','-framerate',String(meta.fps),'-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',output],{stdio:['pipe','ignore','inherit']});
 const completed=once(encoder,'close');
 for(let frame=0;frame<Math.round(meta.duration*meta.fps);frame++){
  if(pageFailure)throw pageFailure;
  await page.evaluate(({t,id})=>{window.__timelines[id].seek(t,true)},{t:frame/meta.fps,id:meta.name});
  const png=await page.screenshot({type:'png'});
  if(!encoder.stdin.write(png))await once(encoder.stdin,'drain');
  if(frame%90===0)console.log(`frame ${frame}/${meta.duration*meta.fps}`);
 }
 encoder.stdin.end();
 const [code]=await completed;
 if(code!==0)throw new Error(`Encoder exited ${code}`);
 console.log(output);
}finally{if(encoder&&encoder.exitCode===null)encoder.kill();await browser.close()}
