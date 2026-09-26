(function(root){
 'use strict';
 function boundsAt(points,x){
  if(x<=points[0][0])return points[0].slice(1);
  if(x>=points.at(-1)[0])return points.at(-1).slice(1);
  const j=points.findIndex(p=>p[0]>=x),a=points[j-1],b=points[j],u=(x-a[0])/(b[0]-a[0]);
  return [a[1]+u*(b[1]-a[1]),a[2]+u*(b[2]-a[2])];
 }
 const angle=-40*Math.PI/180;
 const outline=Array.from({length:360},(_,i)=>{
  const a=i*Math.PI/180,x=12*Math.cos(a),y=10.5*Math.sin(a);
  return [x*Math.cos(angle)-y*Math.sin(angle),x*Math.sin(angle)+y*Math.cos(angle)];
 });
 function place(points,x,lane){
  if(!Number.isFinite(x)||!Number.isFinite(lane)||lane<0||lane>1)throw new Error('Invalid particle position/lane');
  if(points.length<2||points.some((p,i)=>p.length!==3||p.some(v=>!Number.isFinite(v))||p[1]>=p[2]||(i&&points[i-1][0]>=p[0])))throw new Error('Invalid channel support');
  let top=-Infinity,bottom=Infinity;
  for(const [dx,dy]of outline){
   const [a,b]=boundsAt(points,x+dx);
   top=Math.max(top,a-dy+1);bottom=Math.min(bottom,b-dy-1);
  }
  if(top>bottom)throw new Error(`Ellipse cannot fit at ${x}: ${top}..${bottom}`);
  return {x,y:top+(bottom-top)*lane,top,bottom};
 }
 const api={boundsAt,outline,place};
 if(typeof module!=='undefined')module.exports=api;
 root.ParticlePlacement=api;
})(typeof window!=='undefined'?window:globalThis);
