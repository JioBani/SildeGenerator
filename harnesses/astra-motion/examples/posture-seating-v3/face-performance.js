// Local two-state facial performance; no general acting capability promotion.
const head=document.getElementById('head');
const svgNS='http://www.w3.org/2000/svg';
const mouth=[...head.querySelectorAll('path')].find(p=>p.getAttribute('d')==='M12 16Q31 30 52 15');
if(!mouth)throw new Error('Expected reviewed actor mouth');
mouth.id='performanceMouth';
const clip=document.createElementNS(svgNS,'clipPath');clip.id='performanceEyeClip';
const circle=document.createElementNS(svgNS,'circle');
for(const[k,v]of Object.entries({cx:30,cy:-29,r:24}))circle.setAttribute(k,v);
clip.append(circle);head.append(clip);
const lid=document.createElementNS(svgNS,'rect');lid.id='performanceLid';
for(const[k,v]of Object.entries({x:5,y:-54,width:50,height:25,fill:'#fa679b','clip-path':'url(#performanceEyeClip)'}))lid.setAttribute(k,v);
head.append(lid);
const faceTrack=window.__timelines['posture-seating-study'];
mouth.setAttribute('d','M12 19Q31 17 52 19');
faceTrack.to(lid,{attr:{height:0},duration:.25,ease:'power1.inOut'},.25)
 .to(mouth,{attr:{d:'M12 16Q31 30 52 15'},duration:.25,ease:'power1.inOut'},.35)
 .to(lid,{attr:{height:25},duration:.45,ease:'power1.inOut'},10.8)
 .to(mouth,{attr:{d:'M12 19Q31 17 52 19'},duration:.45,ease:'power1.inOut'},10.95)
 .to(lid,{attr:{height:0},duration:.3,ease:'power1.inOut'},18.15)
 .to(mouth,{attr:{d:'M12 16Q31 30 52 15'},duration:.3,ease:'power1.inOut'},18.35);
window.__facePerformance={states:['tired','engaged'],scope:'Reviewed seated actor fixture only',humanApproved:false};
