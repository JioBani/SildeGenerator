const assert=require('node:assert/strict');
const {place,outline,boundsAt}=require('../harnesses/astra-motion/examples/blood-bulge-study-v4/particle-placement.js');
// A 20px channel fits the rotated ellipse, but not the previous 22px disk clearance.
const channel=[[0,100,120],[640,100,120]];
for(const lane of [0,.5,1]){
 const p=place(channel,320,lane);
 for(const [dx,dy]of outline){
  const [a,b]=boundsAt(channel,p.x+dx);
  assert(p.y+dy>=a+.999&&p.y+dy<=b-.999);
 }
}
assert.throws(()=>place([[0,100,110],[640,100,110]],320,.5),/cannot fit/);
assert.throws(()=>place([[10,100,120],[0,100,120]],320,.5),/Invalid channel/);
assert.throws(()=>place(channel,320,2),/Invalid particle/);
assert.deepEqual(place(channel,320,.5),place(channel,320,.5));
console.log('PASS ellipse sampled containment, narrow rejection, input checks, deterministic placement');
