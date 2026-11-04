/* Localised character motion: the scene and feet never move. */
(()=>{
const ns='http://www.w3.org/2000/svg', reduced=matchMedia('(prefers-reduced-motion: reduce)');
let serial=0;
function addMotion(node){
 const sofa=node.classList.contains('sofa-scene'),poppy=node.classList.contains('poppy');
 const eyes=sofa?[[568,341,37,34],[710,310,27,33],[868,331,33,35],[1013,375,39,35]]:poppy?[[982,333,39,43],[1163,372,46,40]]:[[416,352,43,39],[588,320,32,40]];
 const hands=sofa?[[590,555,70,42],[1025,521,45,72]]:poppy?[[1020,675,62,66],[1160,677,65,65]]:[[321,674,60,78],[678,667,37,71]];
 const id='hands-'+(++serial),svg=document.createElementNS(ns,'svg');
 svg.setAttribute('viewBox',sofa?'0 0 1536 1024':poppy?'768 0 768 1024':'0 0 768 1024');
 svg.setAttribute('aria-hidden','true');svg.classList.add('character-detail');
 // Neutral grey outside the hand regions leaves every other pixel stationary.
 const map=`<svg xmlns="${ns}" width="1536" height="1024"><defs><radialGradient id="g"><stop stop-color="rgb(255,128,128)"/><stop offset="1" stop-color="rgb(128,128,128)"/></radialGradient></defs><rect width="1536" height="1024" fill="rgb(128,128,128)"/>${hands.map(([x,y,rx,ry])=>`<ellipse cx="${x}" cy="${y}" rx="${rx}" ry="${ry}" fill="url(#g)"/>`).join('')}</svg>`;
 svg.innerHTML=`<defs><filter id="${id}" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB"><feImage href="data:image/svg+xml,${encodeURIComponent(map)}" result="map"/><feDisplacementMap in="SourceGraphic" in2="map" scale="0" xChannelSelector="R" yChannelSelector="G"/></filter></defs><image href="assets/${sofa?'sofa-watercolour':'friends-shoes'}.webp" width="1536" height="1024" filter="url(#${id})"/>${eyes.map(([x,y,rx,ry])=>`<g class="eyelid" opacity="0"><ellipse cx="${x}" cy="${y}" rx="${rx+3}" ry="${ry+3}" fill="#ffe6a0"/><path d="M ${x-rx} ${y} Q ${x} ${y+ry*.6} ${x+rx} ${y}" fill="none" stroke="#70513c" stroke-width="5" stroke-linecap="round"/></g>`).join('')}`;
 if(sofa){const wrap=document.createElement('div');wrap.className=node.className;wrap.setAttribute('role','img');wrap.setAttribute('aria-label',node.alt);wrap.append(svg);node.replaceWith(wrap);node=wrap}else node.append(svg);
 const lids=[...svg.querySelectorAll('.eyelid')],warp=svg.querySelector('feDisplacementMap');
 function schedule(){if(!node.isConnected)return;setTimeout(()=>{if(!node.isConnected)return;if(!document.hidden&&!reduced.matches){const offset=sofa&&Math.random()>.5?2:0;lids.slice(offset,offset+2).forEach(e=>e.animate([{opacity:0},{opacity:1,offset:.35},{opacity:1,offset:.65},{opacity:0}],{duration:180}));}schedule()},2300+Math.random()*4500)}
 function gesture(){if(!node.isConnected)return;setTimeout(()=>{if(!node.isConnected)return;if(!document.hidden&&!reduced.matches){const start=performance.now(),direction=Math.random()>.5?1:-1;function frame(t){if(!node.isConnected)return;const f=Math.min((t-start)/1100,1);warp.setAttribute('scale',String(Math.sin(f*Math.PI*2)*10*direction));if(f<1&&!reduced.matches)requestAnimationFrame(frame);else warp.setAttribute('scale','0')}requestAnimationFrame(frame)}gesture()},4000+Math.random()*6000)}
 schedule();gesture();
}
function scan(){document.querySelectorAll('.actor:not([data-motion]),img.sofa-scene').forEach(el=>{el.dataset.motion='true';addMotion(el)})}
new MutationObserver(scan).observe(document.getElementById('stage'),{childList:true,subtree:true});scan();
})();
