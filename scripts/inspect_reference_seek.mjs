import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';
const require=createRequire(new URL('../web/package.json',import.meta.url));
const {chromium}=require('@playwright/test');
const root=path.resolve(process.argv[2]),id=process.argv[3],time=Number(process.argv[4]);
const meta=JSON.parse(await fs.readFile(path.join(root,'meta.json'),'utf8'));
const finalTime=meta.duration-1/meta.fps;
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1920,height:1080}});
 await page.goto(pathToFileURL(path.join(root,'index.html')).href);
 async function state(t){return page.evaluate(({id,t})=>{
  window.__timelines[id].seek(t,true);
  return [...document.querySelectorAll('#master *')].map((e,index)=>({index,tag:e.tagName,id:e.id,attrs:[...e.attributes].map(a=>[a.name,a.value]),transform:getComputedStyle(e).transform,opacity:getComputedStyle(e).opacity}));
 },{id,t})}
 await state(0);await state(1.5);await state(3);await state(6.5);await state(9.5);await state(12.2);await state(14);
 const a=await state(time);await page.screenshot();await state(finalTime);await page.screenshot();await state(0);await page.screenshot();const b=await state(time);
 const diffs=a.map((x,i)=>JSON.stringify(x)!==JSON.stringify(b[i])?{before:x,after:b[i]}:null).filter(Boolean);
 await fs.writeFile(path.join(root,'seek-dom-differences.json'),JSON.stringify(diffs,null,2));
 console.log(JSON.stringify(diffs));
}finally{await browser.close()}
