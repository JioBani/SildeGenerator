import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';
const require=createRequire(new URL('../web/package.json',import.meta.url));
const {chromium}=require('@playwright/test');
const root=path.resolve(process.argv[2]);
const v2=process.argv.includes('--v2');
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1920,height:1080}});
 await page.goto(pathToFileURL(path.join(root,'index.html')).href);
 const evidence=await page.evaluate(v2=>{
  const tl=window.__timelines['blood-intervention-study'];
  const $=id=>document.getElementById(id);
  const at=(id,x=0,y=0)=>new DOMPoint(x,y).matrixTransform($(id).getCTM());
  const distance=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y);
  const rows=[];let anchor;
  for(let frame=0;frame<900;frame++){
   const t=frame/30;tl.seek(t,true);
   const balloon=at('balloon'),carrier=at('firstDevice',960,540),implant=at('implant');
   if(t>=23)anchor??=implant;
   const ry=Number($('balloonShape').getAttribute('ry'));
   rows.push({frame,attachmentGap:!v2||t>=12?distance(balloon,carrier):null,retentionDrift:t>=23?distance(implant,anchor):null,
    slidingOffset:balloon.x-carrier.x,
    carriedImplantGap:v2&&t>=19&&t<=22?distance(implant,at('secondDevice',960,540)):null,
    outerClearance:t>=8&&t<=17.5?Math.min(balloon.y-ry-330,750-balloon.y-ry):null,
    carrierX:at('secondDevice',960,540).x});
  }
  tl.seek(v2?15:14,true);
  const upper=$('upperDeposit'),lower=$('lowerDeposit');
  const samples=e=>Array.from({length:1001},(_,i)=>e.getPointAtLength(e.getTotalLength()*i/1000).y);
  const ry=Number($('balloonShape').getAttribute('ry'));
  const contactGap=Math.max(Math.abs(540-ry-Math.max(...samples(upper))),Math.abs(Math.min(...samples(lower))-540-ry));
  const flow=[];
  if(v2)for(const t of [25,26,28,29.9]){
   tl.seek(t,true);
   const cells=[...$('particles').children].map(e=>new DOMPoint(0,0).matrixTransform(e.getCTM()));
   flow.push({t,visible:cells.filter(p=>p.x>0&&p.x<1920&&p.y>330&&p.y<750).length,firstX:cells[0].x,opacity:Number(getComputedStyle($('particles')).opacity)});
  }
  tl.seek(28,true);$('implant').setAttribute('transform','translate(700 540)');
  const mutationDetected=distance(at('implant'),new DOMPoint(960,540))>100;
  return {rows,contactGap,mutationDetected,flow};
 },v2);
 const r={scope:'Fixture attachment, centerline contact and retention only; not a general contact solver or clinical validation',frames:900,
  maxAttachmentGap:Math.max(...evidence.rows.map(r=>r.attachmentGap??0)),
  attachmentScope:v2?'After sleeve acquisition at 12s':'All frames',
  sleeveTravel:v2?evidence.rows[360].slidingOffset-evidence.rows[270].slidingOffset:null,
  maxCarriedImplantGap:v2?Math.max(...evidence.rows.map(r=>r.carriedImplantGap??0)):null,
  maxRetentionDrift:Math.max(...evidence.rows.map(r=>r.retentionDrift??0)),
  minOuterClearance:Math.min(...evidence.rows.map(r=>r.outerClearance??Infinity)),
  carrierWithdrawal:v2?evidence.rows[672].carrierX-evidence.rows[720].carrierX:evidence.rows[720].carrierX-evidence.rows[780].carrierX,
  inflationCenterlineContactGap:evidence.contactGap,mutationDetected:evidence.mutationDetected};
 r.returnFlow=evidence.flow;
 r.pass=r.maxAttachmentGap<.01&&r.maxRetentionDrift<.01&&r.minOuterClearance>=0&&r.carrierWithdrawal>1000&&r.inflationCenterlineContactGap<.1&&r.mutationDetected;
 if(v2)r.pass=r.pass&&r.sleeveTravel>1400&&r.maxCarriedImplantGap<.01&&r.returnFlow.every((p,i,a)=>p.visible>=10&&p.opacity>.99&&(i===0||p.firstX>a[i-1].firstX));
 await fs.writeFile(path.join(root,'interaction-review.json'),JSON.stringify(r,null,2));
 console.log(JSON.stringify(r));if(!r.pass)process.exitCode=1;
}finally{await browser.close()}
