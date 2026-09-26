// Measure rendered font boxes, not character-count estimates or model claims.
import {createRequire} from 'node:module';
import {readFile,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const require=createRequire('/app/hyperframes-runtime/package.json');
const puppeteer=require('puppeteer-core');
const [input,output]=process.argv.slice(2);
if(!input||!output) throw new Error('usage: audit_snapshot_text.mjs index.html report.json');
const browser=await puppeteer.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
try {
  const page=await browser.newPage();
  await page.setViewport({width:1280,height:720});
  await page.goto(pathToFileURL(resolve(input)).href);
  await page.evaluate(async()=>{await document.fonts.ready; const t=window.__timelines['hybrid-story-segment'];t.seek(t.duration()-.001);});
  const report=await page.evaluate(()=>{
    const elements=[...document.querySelectorAll('h2,svg text')];
    const boxes=elements.map((el,i)=>{
      const r=el.getBoundingClientRect();
      return {id:i,text:el.textContent,x:r.x,y:r.y,width:r.width,height:r.height};
    });
    const findings=[];
    for(const b of boxes) if(b.x<40||b.x+b.width>1240||b.y<12||b.y+b.height>556)
      findings.push({kind:'outside_graphic_safe_region',id:b.id});
    for(let i=0;i<boxes.length;i++) for(let j=i+1;j<boxes.length;j++){
      const a=boxes[i],b=boxes[j];
      const x=Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x);
      const y=Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y);
      if(x>2&&y>2) findings.push({kind:'text_overlap',ids:[a.id,b.id]});
    }
    return {boxes,findings,fontLoaded:document.fonts.check('24px "Noto Sans CJK KR"')};
  });
  const negatives=await page.evaluate(()=>{
    const el=document.querySelector('svg text');
    el.setAttribute('y','580');
    const a=el.getBoundingClientRect();
    el.setAttribute('x','-200');
    const b=el.getBoundingClientRect();
    return {caption_collision_detected:a.bottom>556,left_clip_detected:b.left<40};
  });
  const passed=report.fontLoaded&&!report.findings.length&&Object.values(negatives).every(Boolean);
  const result={status:passed?'TEXT_GEOMETRY_PASS':'REVISE',goal_status:'GOAL_NOT_MET',...report,negative_controls:negatives,
    html_sha256:createHash('sha256').update(await readFile(input)).digest('hex'),
    scope:'Final snapshot DOM text bounds at 1280x720 with caption-safe boundary 556px; not OCR or full subtitle inspection',human_approval:null};
  await writeFile(output,JSON.stringify(result,null,2),{flag:'wx'});
  console.log(JSON.stringify({status:result.status,findings:result.findings,negative_controls:negatives}));
  if(!passed) process.exitCode=1;
} finally {await browser.close();}
