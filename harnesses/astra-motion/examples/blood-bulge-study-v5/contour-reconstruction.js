(function(root){
 // Experimental spatial prior: isolated inward spikes may be particle occlusion.
 // This is not segmentation ground truth and may erase genuine narrow structures.
 function reconstruct(points){
  const changes=[];
  const median=a=>{a.sort((x,y)=>x-y);return (a[Math.floor((a.length-1)/2)]+a[Math.floor(a.length/2)])/2};
  const result=points.map((p,i)=>{
   const neighbors=points.slice(Math.max(0,i-2),i+3).filter(q=>q!==p);
   if(neighbors.length<4)return [...p];
   const top=median(neighbors.map(q=>q[1])),bottom=median(neighbors.map(q=>q[2]));
   const a=p[1]-top>6?top:p[1],b=bottom-p[2]>6?bottom:p[2];
   if(a!==p[1]||b!==p[2])changes.push({x:p[0],raw:p.slice(1),inferred:[a,b]});
   return [p[0],a,b];
  });
  return {points:result,changes};
 }
 if(typeof module!=='undefined')module.exports={reconstruct};
 root.ContourReconstruction={reconstruct};
})(typeof window!=='undefined'?window:globalThis);
