import {chromium} from '@playwright/test';
import {createHash} from 'node:crypto';
import {mkdirSync,writeFileSync,readFileSync} from 'node:fs';
import {dirname,resolve,join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const dir=join(root,'experiments/actor-performance'),out=join(dir,'output/standard-actor-v3');
mkdirSync(out,{recursive:true});
const browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_BROWSER_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
try{
 const page=await browser.newPage({viewport:{width:1000,height:820}});
 await page.goto(pathToFileURL(join(dir,'stage.html')).href);
 await page.waitForFunction(()=>!!window.PerformanceStage);
 const pack=await page.evaluate(()=>{
   const s=window.PerformanceStage.draw(0),def=document.querySelector('#art defs').outerHTML;
   const ids=['torso','head','neck-under-shirt','eyes','pupils','brow-left','brow-right','mouth',
     ...['left','right'].flatMap(side=>[side+'-upper',side+'-forearm',side+'-palm',side+'-thigh',side+'-shin','foot-'+side])];
   const substitute=root=>{
     for(const child of [...root.children]){
       if(ids.includes(child.id)){
         const ref=document.createElementNS('http://www.w3.org/2000/svg','g');
         ref.setAttribute('data-part',child.id);
         if(child.hasAttribute('transform'))ref.setAttribute('transform',child.getAttribute('transform'));
         child.replaceWith(ref);
       }else substitute(child);
     }
   };
   const parts=ids.map(id=>{
     const element=document.getElementById(id),b=element.getBBox(),m=element.getCTM(),clone=element.cloneNode(true);
     clone.removeAttribute('transform');
     const inherited=['fill','stroke','stroke-width','stroke-linecap','stroke-linejoin','fill-rule'];
     for(const key of inherited)clone.style.setProperty(key,getComputedStyle(element).getPropertyValue(key));
     let strokePad=0;
     for(const node of [element,...element.querySelectorAll('*')]){
       const style=getComputedStyle(node);
       if(style.stroke==='none')continue;
       const local=m.inverse().multiply(node.getCTM()),{a,b,c,d}=local;
       const sum=a*a+b*b+c*c+d*d,det=a*d-b*c;
       const scale=Math.sqrt((sum+Math.sqrt(Math.max(0,sum*sum-4*det*det)))/2);
       const join=style.strokeLinejoin==='miter'?Number(style.strokeMiterlimit):1;
       strokePad=Math.max(strokePad,parseFloat(style.strokeWidth)*scale*join/2);
     }
     substitute(clone);
     const x=Math.floor(Math.min(0,b.x-strokePad)-4),y=Math.floor(Math.min(0,b.y-strokePad)-4);
     const box=[x,y,Math.ceil(Math.max(0,b.x+b.width+strokePad)+4)-x,Math.ceil(Math.max(0,b.y+b.height+strokePad)+4)-y];
     return {id,viewBox:box,pivot_in_viewbox:[-x,-y],stroke_padding:strokePad,dependencies:[...clone.querySelectorAll('[data-part]')].map(e=>e.dataset.part),rest_local_to_canvas:[m.a,m.b,m.c,m.d,m.e,m.f],
       svg:`<svg xmlns="http://www.w3.org/2000/svg" viewBox="${box.join(' ')}" fill="none" stroke="#283c40" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">${def}${clone.outerHTML}</svg>`};
   });
   const actor=document.getElementById('actor').cloneNode(true),template=actor.cloneNode(true);substitute(template);
   const wrap=body=>`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 820">${def}${body}</svg>`;
   return {parts,assembly_template:wrap(template.outerHTML),reference:wrap(actor.outerHTML),spec:window.ActorPerformance.spec,rest_joints:Object.fromEntries(['hip','neck','shoulderL','shoulderR','elbowL','elbowR','handL','handR','hipL','hipR','kneeL','kneeR','ankleL','ankleR'].map(k=>[k,s[k]]))};
 });
 const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
 for(const part of pack.parts){const filename=part.id+'.svg';writeFileSync(join(out,filename),part.svg);part.path=filename;part.sha256=hash(part.svg);delete part.svg;}
 writeFileSync(join(out,'assembly-template.svg'),pack.assembly_template);
 // Re-import files from disk, rather than comparing two in-memory copies.
 const rebuilt=await page.evaluate(({template,files})=>{
   const parser=new DOMParser(),doc=parser.parseFromString(template,'image/svg+xml');
   function expand(root,stack=[]){
     for(const ref of [...root.querySelectorAll('[data-part]')]){
       const id=ref.getAttribute('data-part');
       if(stack.includes(id)||!files[id])throw Error('invalid_part_dependency:'+id);
       const imported=parser.parseFromString(files[id],'image/svg+xml');
       const part=[...imported.documentElement.children].find(e=>e.id===id);
       if(!part)throw Error('missing_part:'+id);
       const clone=doc.importNode(part,true);
       if(ref.hasAttribute('transform'))clone.setAttribute('transform',ref.getAttribute('transform'));
       expand(clone,[...stack,id]);ref.replaceWith(clone);
     }
   }
   expand(doc.documentElement);
   const ids=[...doc.querySelectorAll('[id]')].map(e=>e.id);
   if(new Set(ids).size!==ids.length)throw Error('duplicate_ids');
   return new XMLSerializer().serializeToString(doc);
 },{template:readFileSync(join(out,'assembly-template.svg'),'utf8'),files:Object.fromEntries(pack.parts.map(p=>[p.id,readFileSync(join(out,p.path),'utf8')]))});
 writeFileSync(join(out,'assembled.svg'),rebuilt);
 await page.setContent('<style>body{margin:0;background:#edf3f5}svg{display:block;width:1000px;height:820px}</style>'+pack.reference);
 const reference=await page.screenshot({path:join(out,'reference.png')});
 await page.setContent('<style>body{margin:0;background:#edf3f5}svg{display:block;width:1000px;height:820px}</style>'+rebuilt);
 const actual=await page.screenshot({path:join(out,'assembled.png')});
 assert.ok(reference.equals(actual),'Neutral assembly must match source pixels exactly');
 delete pack.reference;delete pack.assembly_template;
 const manifest={version:'astra-standard-vector-actor-draft-0.3',...pack,
   assembly:{template:'assembly-template.svg',template_sha256:hash(readFileSync(join(out,'assembly-template.svg'))),rebuilt:'assembled.svg',rebuilt_sha256:hash(rebuilt),neutral_pixel_exact:true,reference_png_sha256:hash(reference),assembled_png_sha256:hash(actual),scope:'Neutral assembly only; animated re-import is not yet verified'},
   source_hashes:Object.fromEntries(['skin.js','performance.js','../layered-motion/actor.js','../../web/e2e/export-standard-actor.mjs'].map(p=>[p,hash(readFileSync(join(dir,p)))])),
   provenance:'Existing Astra authored vectors, not detector output or anatomical ground truth',
   production_ready:false,human_design_review:'PENDING',human_acting_review:'PENDING',
   motion_candidate:'notice_reach',garment_policy:'Rigid segment skin; preserve collar in front of neck underlay',
   design_replacement_policy:'Keep local canvases, landmarks and limb lengths. New artwork invalidates previous design/acting review.'};
 writeFileSync(join(out,'manifest.json'),JSON.stringify(manifest,null,2));
 console.log(JSON.stringify({parts:pack.parts.length,output:out,neutral_pixel_exact:true,production_ready:false}));
}finally{await browser.close();}
