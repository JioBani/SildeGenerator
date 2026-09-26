// Observe visible SVG labels throughout the actual GSAP schedule.
import {createRequire} from 'node:module';
import {readFile,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const require=createRequire('/app/hyperframes-runtime/package.json');
const puppeteer=require('puppeteer-core');
const [input,output]=process.argv.slice(2);
if(!input||!output) throw new Error('index.html and report.json required');
const browser=await puppeteer.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
try {
 const page=await browser.newPage(); await page.setViewport({width:1280,height:720});
 await page.goto(pathToFileURL(resolve(input)).href);
 const result=await page.evaluate(async()=>{
  await document.fonts.ready;
  const timeline=window.__timelines['hybrid-story-segment']; const samples=[];
  function measure() {
   const boxes=[...document.querySelectorAll('h2,svg text')].filter(el=>{
    for(let p=el;p;p=p.parentElement) if(Number(getComputedStyle(p).opacity)<.9) return false;
    return true;
   }).map(el=>{const r=el.getBoundingClientRect();return {text:el.textContent,x:r.x,y:r.y,width:r.width,height:r.height};});
   const findings=[];
   for (const b of boxes) if(b.x<40||b.x+b.width>1240||b.y<12||b.y+b.height>556) findings.push({kind:'safe_area',text:b.text});
   for(let i=0;i<boxes.length;i++) for(let j=i+1;j<boxes.length;j++){
    const a=boxes[i],b=boxes[j];
    if(Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x)>2 && Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y)>2)
      findings.push({kind:'text_overlap',texts:[a.text,b.text]});
   }
   return {boxes,findings};
  }
  for(let t=.1;t<timeline.duration();t+=.1){timeline.seek(t);const m=measure();samples.push({time:t,...m});}
  timeline.seek(timeline.duration()-.02);
  const text=[...document.querySelectorAll('svg text')].find(el=>{
    for(let p=el;p;p=p.parentElement) if(Number(getComputedStyle(p).opacity)<.9) return false;
    return true;
  });
  if(!text) throw new Error('no_visible_svg_text_for_negative_control');
  text.setAttribute('y','580');
  const negative=measure().findings.some(f=>f.kind==='safe_area');
  const serifUsed=[...document.querySelectorAll('h2,svg text')].some(el=>
    getComputedStyle(el).fontFamily.includes('Noto Serif CJK KR'));
  return {fontLoaded:document.fonts.check('24px "Noto Sans CJK KR"'),
    serifLoaded:!serifUsed||document.fonts.check('24px "Noto Serif CJK KR"'),
    samples,negative_caption_collision_detected:negative};
 });
 const failed=result.samples.filter(s=>s.findings.length);
 const report={status:!failed.length&&result.fontLoaded&&result.serifLoaded&&result.negative_caption_collision_detected?'TEXT_GEOMETRY_PASS':'REVISE',...result,
  html_sha256:createHash('sha256').update(await readFile(input)).digest('hex'),goal_status:'GOAL_NOT_MET',human_approval:null,
  scope:'Visible DOM text boxes at 100ms intervals, 1280x720, subtitle-safe boundary 556px. Not final pixel OCR.'};
 await writeFile(output,JSON.stringify(report,null,2),{flag:'wx'});
 console.log(JSON.stringify({status:report.status,failed_samples:failed.length,first_fail:failed[0]}));
 if(report.status==='REVISE') process.exitCode=1;
} finally {await browser.close();}
