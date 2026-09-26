// Export independently authored DOM geometry, never reference video pixels.
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
const require=createRequire(new URL('../web/package.json',import.meta.url));
const {chromium}=require('@playwright/test');
const [context,alignment,out]=process.argv.slice(2).map(p=>path.resolve(p));
await fs.mkdir(out,{recursive:false});
const browser=await chromium.launch({channel:'chrome',headless:true});
const records=[];
try{
 for(const [root,id,selector,name] of [[context,'posture-context-study','#transit','transit.svg'],[alignment,'posture-alignment-study','#front','front.svg']]){
  const page=await browser.newPage();
  await page.goto(pathToFileURL(path.join(root,'index.html')).href);
  await page.waitForFunction(id=>Boolean(window.__timelines?.[id]),id);
  const svg=await page.evaluate(({id,selector})=>{
   window.__timelines[id].seek(0,true);
   const node=document.querySelector(selector).cloneNode(true);
   // Export the geometry at the shared handoff pose, without a hidden camera.
   node.removeAttribute('style');
   if(selector==='#transit')node.removeAttribute('transform');
   const container=document.createElementNS('http://www.w3.org/2000/svg','svg');
   container.setAttribute('viewBox','0 0 640 360');
   container.setAttribute('width','640');container.setAttribute('height','360');
   container.append(node);
   return new XMLSerializer().serializeToString(container);
  },{id,selector});
  await fs.writeFile(path.join(out,name),svg);
  records.push({name,source:path.relative(process.cwd(),root),selector,sha256:crypto.createHash('sha256').update(svg).digest('hex')});
  await page.close();
 }
 await fs.writeFile(path.join(out,'manifest.json'),JSON.stringify({status:'EXPERIMENTAL_INDEPENDENT_ART',human_approved:false,records},null,2));
 console.log(JSON.stringify(records));
}finally{await browser.close()}
