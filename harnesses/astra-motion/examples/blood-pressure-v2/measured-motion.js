// Experimental source-aligned track; not a general vessel or physiology model.
const measured = window.measuredWalls;
if (!measured?.rows?.length) throw new Error('Missing reviewed wall measurement');
const track = window.__timelines['blood-pressure-study'];
const paths = [...document.querySelector('#walls').children];
const pathFor = points => {
  const extended = [[-500, points[0][1]*3], ...points.map(([x,y])=>[x*3,y*3]), [2400,points.at(-1)[1]*3]];
  return extended.map(([x,y],i)=>(i?'L':'M')+x+' '+y).join('');
};
const approximate = (base,sign,t) => {
  const points=[];
  for(let x=-500;x<=2400;x+=40) points.push([x,base+sign*48*Math.max(0,Math.cos(x/210-t*Math.PI*2/2.2))**6]);
  return points.map(([x,y],i)=>(i?'L':'M')+x+' '+y).join('');
};
for(let side=0;side<2;side++){
  const targets=paths.slice(side*4,side*4+4);
  const base=side?730:345,sign=side?1:-1;
  let previous=0;
  for(let t=.25;t<8;t+=.25){
    track.to(targets,{attr:{d:approximate(base,sign,t)},duration:t-previous,ease:'none'},previous);
    previous=t;
  }
  for(const row of measured.rows){
    const t=row.source_second-57;
    track.to(targets,{attr:{d:pathFor(side?row.lower:row.upper)},duration:t-previous,ease:'none'},previous);
    previous=t;
  }
  // Hold the last measured geometry during the exit; no invented continuation.
}
window.__wallMeasurementScope={sourceStart:65,sourceEnd:78,sourceSha256:measured.source_sha256};
