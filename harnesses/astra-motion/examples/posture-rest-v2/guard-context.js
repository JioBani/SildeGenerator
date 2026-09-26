// The source depicts a uniformed guard in a sentry box, not internal anatomy.
const guard=document.getElementById('scanner');guard.replaceChildren();
guard.dataset.semanticRole='uniformed_guard_in_sentry_box';
function node(tag,attrs,parent=guard){const e=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);parent.append(e);return e}
node('rect',{width:1002,height:1080,fill:'#03415d'});
node('rect',{x:365,width:637,height:1080,fill:'#065d86'});
node('path',{id:'sentryBox',d:'M510 1080V205Q510 38 682 38Q855 38 855 205V1080Z',fill:'#a1a0ac'});
node('path',{d:'M645 773H755V1080H645Z',fill:'#03415d'});
const actor=node('g',{id:'guardActor'});
node('path',{id:'guardFace',d:'M664 218H755V263Q750 323 690 305Q657 290 664 218Z',fill:'#fa6397'},actor);
node('path',{d:'M753 223H786Q808 224 790 249H752Z',fill:'#d93570'},actor);
node('ellipse',{cx:730,cy:232,rx:29,ry:22,fill:'#fff3dc'},actor);
node('circle',{cx:737,cy:230,r:16,fill:'#03415d'},actor);
node('path',{d:'M666 224Q660 270 737 280',stroke:'#03415d','stroke-width':17,fill:'none'},actor);
node('path',{id:'guardHat',d:'M600-80H788V221H663V277Q600 268 600 214Z',fill:'#03415d'},actor);
node('path',{id:'tunic',d:'M626 568V390Q626 334 688 337Q750 337 750 390V598Q800 642 800 682V787H596V682Q596 615 626 598Z',fill:'#d73570'},actor);
node('rect',{x:626,y:567,width:124,height:32,fill:'#fff4df'},actor);
node('path',{d:'M724 344V567',stroke:'#fff4df','stroke-width':7},actor);
for(let i=0;i<5;i++)node('circle',{cx:714,cy:389+i*35,r:7,fill:'#fff4df','data-role':'uniform-button'},actor);
node('path',{d:'M654 363V741',stroke:'#bd265b','stroke-width':44,'stroke-linecap':'round'},actor);
node('path',{d:'M654 363V390',stroke:'#03415d','stroke-width':38,'stroke-linecap':'round'},actor);
node('rect',{x:651,y:724,width:44,height:55,fill:'#fff4df'},actor);
node('path',{d:'M652 807Q650 770 677 777Q724 779 697 813Q700 846 674 846Q649 843 652 807Z',fill:'#fa6397'},actor);
window.__guardContext={semanticRole:'uniformed_guard_in_sentry_box',anatomicalOverlay:false,evidence:'posture-scan-source.png',humanApproved:false};
