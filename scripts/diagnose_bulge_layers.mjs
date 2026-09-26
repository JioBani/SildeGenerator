import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';
const require=createRequire(new URL('../web/package.json',import.meta.url));
const {chromium}=require('@playwright/test');
const [root,out]=process.argv.slice(2).map(p=>path.resolve(p));
await fs.mkdir(out,{recursive:false});
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1920,height:1080}});
 page.on('pageerror',error=>console.error(error.message));
 await page.goto(pathToFileURL(path.join(root,'index.html')).href);
 await page.waitForFunction(()=>Boolean(window.__timelines?.['blood-bulge-study']));
 for(const t of [0,4])for(const mode of ['full','no-particles','no-edges','geometry']){
  await page.evaluate(({t,mode})=>{
   window.__timelines['blood-bulge-study'].seek(t,true);
   document.querySelector('#particles').style.visibility=['no-particles','geometry'].includes(mode)?'hidden':'visible';
   for(const p of document.querySelectorAll('path[stroke="#850c04"]'))p.style.visibility=['no-edges','geometry'].includes(mode)?'hidden':'visible';
  },{t,mode});
  await fs.writeFile(path.join(out,`${t}-${mode}.png`),await page.screenshot());
 }
}finally{await browser.close()}
