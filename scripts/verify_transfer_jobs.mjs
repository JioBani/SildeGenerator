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
 await page.waitForFunction(()=>window.transferJobs?.length===6);
 const report=await page.evaluate(({sharedFocus,corruptFocus})=>{
  if(corruptFocus)document.querySelector('[data-parallel-job="A"]').setAttribute('data-focus-id','wrong-calculation');
  const focused=document.querySelector('[data-view="system"][data-focus-id]');
  const mappingPass=!sharedFocus||(
   window.transferJobs.map(j=>j.id).join('')==='ABCDEF'&&
   document.querySelectorAll('[data-parallel-job]').length===6&&
   focused?.getAttribute('data-parallel-job')==='A'&&
   [...document.querySelectorAll('[data-focus-id]')].every(n=>n.getAttribute('data-focus-id')===window.studyConfig.focus.id)
  );
  const rows=[];
  for(let frame=0;frame<475;frame++){
   const t=frame/30;window.__timelines['context-reveal-study'].seek(t,true);
   const counts={sequential:0,parallel:0};let pass=true;
   for(const job of window.transferJobs)for(const mode of ['sequential','parallel']){
    const state=t<job[mode+'Start']?'pending':t<job[mode+'End']?'active':'completed';
    const node=document.querySelector(`[data-${mode}-job="${job.id}"]`);
    pass&&=node.getAttribute('data-state')===state;
    const marker=node.querySelector('[data-job-marker]');
    pass&&=marker!==null&&marker.textContent===job.id&&getComputedStyle(marker).opacity==='1';
    if(node.getAttribute('data-state')==='active')counts[mode]++;
   }
   pass&&=counts.sequential<=1&&(counts.parallel===0||counts.parallel===6);
   rows.push({frame,t,...counts,pass});
  }
  return {pass:mappingPass&&rows.every(r=>r.pass),mappingPass,rows,jobs:window.transferJobs,
   limitations:'Authored state schedule only, not GPU performance measurement, visual identity continuity, pronunciation or comprehension approval.'};
 },{sharedFocus:process.argv.includes('--shared-focus'),corruptFocus:process.argv.includes('--corrupt-focus')});
 await fs.writeFile(path.join(root,'jobs-review.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify({pass:report.pass,mappingPass:report.mappingPass,frames:report.rows.length,failures:report.rows.filter(r=>!r.pass).slice(0,4)}));
 if(!report.pass)process.exitCode=1;
}finally{await browser.close()}
