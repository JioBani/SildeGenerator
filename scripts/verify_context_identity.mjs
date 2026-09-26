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
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(path.join(root,'index.html')).href);
 await page.waitForFunction(()=>Boolean(window.__timelines?.['context-reveal-study']));
 async function inspect(t){return page.evaluate(t=>{
  window.__timelines['context-reveal-study'].seek(t,true);
  const f=window.studyConfig.focus,failures=[];
  const reps=[...document.querySelectorAll('[data-focus-id]')];
  if(reps.length!==3)failures.push('representation-count');
  const views=reps.map(n=>n.dataset.view).sort();
  if(JSON.stringify(views)!==JSON.stringify(['detail','local','system']))failures.push('views');
  for(const n of reps){
   const v=n.dataset.view;
   if(n.dataset.focusId!==f.id)failures.push(v+':identity');
   if(n.querySelector('[data-role="identity-marker"]')?.textContent!==f.marker)failures.push(v+':marker');
   if(n.querySelector('[data-role="identity-color"]')?.getAttribute('fill')!==f.color)failures.push(v+':color');
   const result=n.querySelector('[data-role="result"]'),operation=n.querySelector('[data-role="operation"]');
   if(result?.textContent!==String(f.output))failures.push(v+':result');
   const expected=t>=1.8?'completed':t>=.7?'active':'pending';
   if(n.dataset.state!==expected)failures.push(v+':state');
   if(Number(getComputedStyle(result).opacity)!==(t>=1.8?1:0))failures.push(v+':result-visibility');
   if(Number(getComputedStyle(operation).opacity)!==(t>=1.8?0:1))failures.push(v+':operation-visibility');
   if(v==='system'&&Number(n.dataset.unit)!==f.unitIndex)failures.push('system:unit-index');
  }
  if(t>=8)for(const id of ['system-board','system-caption']){
   const b=document.getElementById(id).getBoundingClientRect();
   if(b.left<window.innerWidth/2||b.right>window.innerWidth||b.top<0||b.bottom>window.innerHeight)failures.push(id+':clipped');
  }
  return {time:t,failures};
 },t)}
 const rows=[];
 for(let frame=0;frame<360;frame++)rows.push(await inspect(frame/30));
 // Negative controls check the rendered fields, not only declared identity metadata.
 const mutations=[['identity-marker','textContent','B'],['identity-color','fill','#000000'],['result','textContent','999']];
 const controls=[];
 for(const[role,property,value]of mutations){
  const selector=`[data-view="system"] [data-role="${role}"]`;
  const old=await page.$eval(selector,(n,p)=>p==='textContent'?n.textContent:n.getAttribute(p),property);
  await page.$eval(selector,(n,{property,value})=>property==='textContent'?n.textContent=value:n.setAttribute(property,value),{property,value});
  const result=await inspect(8);controls.push({role,rejected:result.failures.length>0,failures:result.failures});
  await page.$eval(selector,(n,{property,value})=>property==='textContent'?n.textContent=value:n.setAttribute(property,value),{property,value:old});
 }
 const width=await page.$eval('#system-board',n=>n.getAttribute('width'));
 await page.$eval('#system-board',n=>n.setAttribute('width',1000));
 const oversized=await inspect(8);controls.push({role:'layout',rejected:oversized.failures.includes('system-board:clipped'),failures:oversized.failures});
 await page.$eval('#system-board',(n,w)=>n.setAttribute('width',w),width);
 const pass=!errors.length&&rows.every(r=>!r.failures.length)&&controls.every(c=>c.rejected);
 await fs.writeFile(path.join(root,'identity-review.json'),JSON.stringify({pass,errors,frames:rows,negative_controls:controls,
  limitations:'DOM state and rendered-field consistency only; not pixel occlusion, perceived continuity, scientific accuracy or human approval.'},null,2));
 console.log(JSON.stringify({pass,frames:rows.length,failures:rows.filter(r=>r.failures.length).slice(0,5),controls,errors}));
 if(!pass)process.exitCode=1;
}finally{await browser.close()}
