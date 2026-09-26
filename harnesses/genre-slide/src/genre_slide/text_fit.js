// Expose the timeline only after font-aware layout checks, never hide overflow.
document.fonts.ready.then(() => {
  const checks=[];
  for (const scene of document.querySelectorAll('.scene')) {
    for (const node of scene.querySelectorAll('.visual-label')) {
      let size=32;
      const fits=()=>node.scrollHeight<=node.clientHeight+1 && node.scrollWidth<=node.clientWidth+1;
      while(!fits() && size>26) node.style.fontSize=`${--size}px`;
      checks.push({scene:scene.id,element:'.visual-label',fontSize:size,pass:fits()});
    }
    for (const [selector,minSize,maxHeight] of [['h2',32,150],['.caption',28,130],['.credit',20,60]]) {
      const node=scene.querySelector(selector);
      if (!node) continue;
      node.style.height=`${maxHeight}px`;
      let size=parseFloat(getComputedStyle(node).fontSize);
      const fits=()=>node.scrollHeight<=node.clientHeight+1 && node.scrollWidth<=node.clientWidth+1;
      while(!fits() && size>minSize) node.style.fontSize=`${--size}px`;
      checks.push({scene:scene.id,element:selector,fontSize:size,pass:fits()});
    }
  }
  const pass=checks.every(check=>check.pass);
  window.__genreLayoutReview={pass,checks};
  if (!pass) throw new Error('GENRE_TEXT_OVERFLOW: split the scene or shorten its visual heading; preserve narration');
  window.__timelines['__COMPOSITION_ID__']=tl;
});
