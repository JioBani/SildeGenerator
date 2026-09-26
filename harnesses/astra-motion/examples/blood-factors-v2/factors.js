// Original schematic assets; body and heart reuse independent study geometry.
const master=document.getElementById('master');
master.dataset.compositionId='blood-factors-study';master.dataset.duration='24';
const svg=master.querySelector('svg'),bodyPanel=document.getElementById('bodyPanel');
document.getElementById('field').setAttribute('display','none');
bodyPanel.setAttribute('transform','translate(0 0)');
document.getElementById('bodyTitle').setAttribute('opacity','1');
function el(tag,attrs,parent=svg){const e=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);parent.append(e);return e}
const panels=el('g',{id:'factorPanels'}),particleGroups=[];
const vesselClip=el('clipPath',{id:'factorVesselClip'},svg.querySelector('defs'));
el('rect',{width:1920,height:1080},vesselClip);
function vessel(parent,id,color){
 const group=el('g',{id,'clip-path':'url(#factorVesselClip)'},parent);
 el('rect',{width:1920,height:1080,fill:color},group);
 for(const y of [325,755]){
  el('path',{d:`M0 ${y}H1920`,stroke:'#a42b25','stroke-width':100},group);
  el('path',{d:`M0 ${y}H1920`,stroke:'#ec6550','stroke-width':44,'stroke-dasharray':'27 7'},group);
 }
 const particles=el('g',{},group);particleGroups.push(particles);
 for(let i=0;i<36;i++){
  const p=el('g',{transform:`translate(${(i%18)*135} ${430+Math.floor(i/18)*190})`},particles);
  el('ellipse',{rx:40,ry:59,fill:i%3?'#a7211e':'#ece5d2',transform:'rotate(35)'},p);
  if(i%3)el('path',{d:'M0-55V55',stroke:'#6c0000','stroke-width':8},p);
 }
 return group;
}
const small=[];
for(let i=0;i<3;i++){
 const panel=el('g',{id:`inset${i}`,transform:`translate(${i*640} 710) scale(.333333)`,opacity:0},panels);
 vessel(panel,`insetVessel${i}`,i===1?'#145b50':'#790900');
 el('rect',{width:1920,height:1080,fill:'none',stroke:'#fff3d8','stroke-width':22},panel);small.push(panel);
}
const mainVessel=vessel(svg,'factorVessel','#790900');mainVessel.setAttribute('opacity','0');
const sideHeart=el('g',{id:'sideHeart',transform:'translate(1280 0)',opacity:0});
el('rect',{width:960,height:1080,fill:'#450000'},sideHeart);
const network=document.getElementById('circuits').cloneNode(true);network.removeAttribute('id');sideHeart.append(network);
el('use',{href:'#heartArt',transform:'translate(320 580) scale(1.05)'},sideHeart);
el('path',{d:'M0 0V1080',stroke:'#fff0d0','stroke-width':16},sideHeart);
const saltPanel=el('g',{id:'saltPanel',transform:'translate(1920 350)',opacity:0});
el('rect',{width:960,height:730,fill:'url(#paper)'},saltPanel);
const shaker=el('g',{id:'shaker',transform:'translate(420 210) rotate(22)'},saltPanel);
el('rect',{x:-100,y:-160,width:200,height:310,rx:30,fill:'#63c2b1',stroke:'#28776c','stroke-width':12},shaker);
el('path',{d:'M-35-150V130M40-150V130',stroke:'#28776c','stroke-width':9},shaker);
el('rect',{x:-115,y:130,width:230,height:75,rx:20,fill:'#aaa995'},shaker);
for(let x=-65;x<=65;x+=65)el('circle',{cx:x,cy:180,r:10,fill:'#686959'},shaker);
const grains=el('g',{id:'saltGrains'},saltPanel);
for(let i=0;i<16;i++)el('rect',{id:`grain${i}`,x:-9,y:-9,width:18,height:18,fill:'#d9ca84',opacity:0},grains);
el('path',{d:'M140 650Q170 530 390 560Q660 540 700 650Z',fill:'#dc1228'},saltPanel);
const micro=el('g',{id:'microPanel',transform:'translate(1920 0)'});
el('rect',{width:1920,height:1080,fill:'#247a70'},micro);
const dots=el('g',{id:'microDots'},micro);
for(let i=0;i<108;i++)el('circle',{cx:100+i%12*158,cy:95+Math.floor(i/12)*112,r:16,fill:'#a3f6e4',opacity:.35+(i%4)*.2},dots);
const cube=el('g',{id:'saltCube',transform:'translate(820 420)'},micro);
el('rect',{width:250,height:300,fill:'#fffef6'},cube);
el('path',{d:'M250 0V300H0Z',fill:'#efebe8'},cube);
const t=gsap.timeline({paused:true});
t.to(small,{opacity:1,duration:.35,stagger:.45},3)
 .to('#body',{attr:{transform:'translate(960 330) scale(.95)'},duration:.7},5.5)
 .to(panels,{opacity:0,duration:.4},6)
 .set(mainVessel,{opacity:1},6).set(sideHeart,{opacity:1},6)
 .to(mainVessel,{attr:{transform:'translate(-300 0)'},duration:.7,ease:'power2.inOut'},6)
 .to(sideHeart,{attr:{transform:'translate(960 0)'},duration:.7,ease:'power2.inOut'},6)
 .set(saltPanel,{opacity:1},12)
 .to(saltPanel,{attr:{transform:'translate(960 350)'},duration:.6,ease:'power2.inOut'},12)
 .to(shaker,{attr:{transform:'translate(420 210) rotate(32)'},duration:.2,repeat:7,yoyo:true,ease:'none'},13)
 .to(micro,{attr:{transform:'translate(0 0)'},duration:.7,ease:'power2.inOut'},16)
 .to('#microDots circle',{attr:{r:20},duration:.8,repeat:3,yoyo:true,stagger:.003},16.7)
 .to(micro,{attr:{transform:'translate(-1920 0)'},duration:.7,ease:'power2.inOut'},21)
 .set(saltPanel,{opacity:0},21).set(sideHeart,{opacity:0},21)
 .to(mainVessel,{attr:{transform:'translate(0 0)'},duration:.7},21)
 .to({}, {duration:.1},23.9);
for(const group of particleGroups)t.to(group,{attr:{transform:'translate(-270 0)'},duration:3,repeat:7,ease:'none'},0);
window.__grainFlights=[];
for(let i=0;i<16;i++){
 const start=13.3+i*.08,duration=.7,phase=(start-13)/.2,cycle=Math.floor(phase),u=phase-cycle;
 const angle=(22+10*(cycle%2?1-u:u))*Math.PI/180;
 const holeX=[-65,0,65][i%3],holeY=180;
 const x=420+holeX*Math.cos(angle)-holeY*Math.sin(angle),y=210+holeX*Math.sin(angle)+holeY*Math.cos(angle);
 const grain=document.getElementById(`grain${i}`);
 grain.setAttribute('transform',`translate(${x} ${y})`);
 t.set(grain,{opacity:1},start);
 for(let n=1;n<=21;n++){
  const q=n/21,xx=x+45*q,yy=y+(548-y)*q*q;
  t.to(grain,{attr:{transform:`translate(${xx} ${yy})`},duration:duration/21,ease:'none'},start+(n-1)*duration/21);
 }
 window.__grainFlights.push({id:`grain${i}`,start,end:start+duration,holeX,holeY});
}
window.__timelines={'blood-factors-study':t};
