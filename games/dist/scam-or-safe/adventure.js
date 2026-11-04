'use strict';
const stage=document.getElementById('stage'),game=new ScamAdventure();
const portrait=window.matchMedia('(orientation: portrait)');
const mobileDevice=/Android|iPhone|iPad|iPod/i.test(navigator.userAgent)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
const needsRotation=()=>mobileDevice&&portrait.matches;
let page='guidelines';
const music=new GameMusic();
function musicLabel(){const on=music.enabled&&music.ctx?.state==='running';const button=document.getElementById('sound');button.textContent=on?'♫ Music on':'♫ Music off';button.setAttribute('aria-pressed',String(on));button.setAttribute('aria-label',on?'Turn music off':'Turn music on')}
async function startMusic(){await music.start();musicLabel()}
const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const stars=()=>`<ol class="stars" aria-label="${game.stars} of 8 Safety Stars">${Array.from({length:8},(_,i)=>`<li class="${i<game.stars?'collected':''}" aria-label="Star ${i+1}${i<game.stars?' collected':''}">★</li>`).join('')}</ol>`;
const friends=()=>'<img class="sofa-friends" src="assets/sofa-watercolour.webp" alt="Peep and Poppy on their sofa behind a table">';
function go(next,push=true){page=next;if(push)history.pushState({page},'');render()}
function bind(id,fn){const e=document.getElementById(id);if(e)e.onclick=fn}
function render(){document.body.classList.toggle('playing',page==='play'&&!needsRotation());document.getElementById('back').hidden=page==='guidelines';if(page==='guidelines')guidelines();else if(page==='mission')mission();else if(page==='ready'||page==='play'&&needsRotation())ready();else if(page==='finish')finish();else play();window.scrollTo(0,0);stage.querySelector('h1')?.focus({preventScroll:true})}
function guidelines(){stage.innerHTML=`<section class="guidelines"><div class="welcome-nav"><a class="all-games-link" href="../">&lsaquo; All games</a><span>1 of 2 &middot; Before we play</span></div><div class="welcome-heading"><img src="assets/study-watercolour.webp" alt="Peep, Poppy and Professor Ollie in his study"><div><p class="eyebrow">STOP • THINK • CHECK</p><h1 tabindex="-1">Peep &amp; Poppy’s Scam-Spotting Club</h1><p>Professor Ollie has some friendly tips for checking messages and staying safe online.</p></div></div><ul class="safety-rules">${rules.map(([icon,title,detail])=>`<li><strong><span aria-hidden="true">${icon}</span> ${title}</strong>${detail}</li>`).join('')}</ul><div class="welcome-bottom"><button class="primary" id="mission">Next: our adventure</button><p>Read together with a trusted grown-up.</p></div></section>`;bind('mission',()=>go('mission'))}
function mission(){
  warmScene(0);
  stage.innerHTML = `
    <section class="mission-bruno-like">
      <div class="welcome-nav">
        <a class="all-games-link" href="../">&lsaquo; All games</a>
        <span>2 of 2 &middot; Before we play</span>
      </div>

      <div class="mission-card">
        <img
          class="mission-hero"
          src="assets/study-watercolour.webp"
          alt="Peep, Poppy and Professor Ollie in his cosy study"
        >

        <div class="mission-copy">
          <h1 tabindex="-1">Peep &amp; Poppy: Scam or Safe?</h1>

          <p class="mission-description">
            Join Peep and Poppy on a cyber-smart adventure! Look closely at
            messages and websites, spot the clues, and discover how to stay
            safe online.
          </p>

          <button class="primary" id="start">Click to start game</button>

          <p class="mission-help">
            Turn your phone sideways to play. Use the arrows to move and the hand to choose.
          </p>
        </div>
      </div>
    </section>
  `;
  bind('start',()=>{game.reset();startMusic();go(needsRotation()?'ready':'play')});
}
function ready(){const resume=page==='play';stage.innerHTML=`<section class="ready"><p class="eyebrow">Peep &amp; Poppy</p><h1 tabindex="-1">Cyber Smart Officers</h1>${friends()}${needsRotation()?'<div class="orientation-icon" aria-hidden="true">↻</div>':''}<h2>${needsRotation()?'Turn your phone sideways':'Ready for our adventure?'}</h2><p>${needsRotation()?'Play in landscape to see Peep, Poppy and the email together.':'Help our friends check every email before they click.'}</p>${needsRotation()?'<p class="small">Your adventure will appear when you turn your screen.</p>':`<button class="primary" id="enter">${resume?'Continue our adventure':'Let’s investigate'}</button>`}<p class="small">8 levels · 8 Safety Stars · 1 Cyber Smart Badge</p></section>`;bind('enter',()=>go('play'))}
function chime(win=false){if(win)music.victory();else if(music.ctx)music.note(79,music.ctx.currentTime+.02,.3,.10)}
function mailHTML(e){return `<div class="email"><div class="mail-heading"><span aria-hidden="true">✉</span><div><small>${e.kind==='school'||e.kind==='website'?'Website':'From'}</small><strong>${esc(e.sender)}</strong></div></div><h2>${esc(e.title)}</h2>${e.expected?`<div class="addresses"><span>Usual website: <b>${e.expected}</b></span><span>Email’s link: <b>${e.actual}</b></span></div>`:''}<p class="email-message">${esc(e.message).replace(/\n/g,'<br>')}</p>${e.fakeButton?`<div class="fake-action">${e.fakeButton}</div>`:''}${e.link?`<p class="fake-link">${e.link}</p>`:''}${e.note?`<p class="clue-note">${e.note}</p>`:''}<div class="case-dialogue">${e.dialogue.map(([name,line])=>`<p><strong>${name}:</strong> “${esc(line)}”</p>`).join('')}</div><p class="pretend">A pretend example for our game — its links cannot open.</p></div>`}
// Cache loaded, decoded artwork and keep it alive between level renders.
const sceneImages=new Map(),sceneReady=new Set();
function loadSceneImage(src){
 if(sceneImages.has(src))return sceneImages.get(src).promise;
 const image=new Image();image.decoding='async';
 const promise=new Promise((resolve,reject)=>{
  image.onload=async()=>{try{await image.decode();sceneReady.add(src);resolve()}catch(error){sceneImages.delete(src);reject(error)}};
  image.onerror=()=>{sceneImages.delete(src);reject(new Error('Scene image unavailable'))};
 });
 sceneImages.set(src,{image,promise});image.src=src;return promise;
}
function sceneAssets(room){return [room.art,room.sofa?'assets/sofa-watercolour.webp':'assets/friends-shoes.webp',...(room.guest?['../cyber-detectives/assets/toby.png']:[])]}
function prepareScene(index){return Promise.all(sceneAssets(rooms[index]).map(loadSceneImage))}
function warmScene(index){if(rooms[index])prepareScene(index).catch(()=>{});}
function play(){
 if(game.phase==='finish'){go('finish');return}
 const index=game.room;
 if(!sceneAssets(game.place).every(src=>sceneReady.has(src))){
  stage.innerHTML='<section class="scene-loading paper" role="status" aria-live="polite" aria-busy="true"><h1>Getting our next adventure ready…</h1><p>Loading the scene for Level '+(index+1)+'.</p></section>';
  prepareScene(index).then(()=>{if(page==='play'&&game.room===index)play()}).catch(()=>{
   if(page!=='play'||game.room!==index)return;
   stage.innerHTML='<section class="scene-loading paper" role="alert"><h1>Let’s try loading the scene again</h1><p>Please check your connection, then try again.</p><button class="primary" id="retry-scene">Try again</button></section>';
   bind('retry-scene',play);
  });return;
 }
 warmScene(index+1);
 drawPlay();
}
function drawPlay(){const r=game.place,e=game.email,p=game.phase;if(p==='finish'){go('finish');return}const speaking=p==='talk'?r.talk[game.line][0]:'';stage.innerHTML=`<section class="play-shell"><div class="hud"><div><span class="eyebrow">Level ${game.room+1} of 8</span><h1 tabindex="-1">${r.name}</h1></div><div class="hud-title">Cyber Smart Officers</div><div class="score"><span>Safety Stars: ${game.stars} / 8</span>${stars()}</div></div><div class="world phase-${p} room-${game.room}"><img class="backdrop" src="${r.art}" alt="Watercolour ${r.location.toLowerCase()}">${r.sofa?`<img class="sofa-scene ${speaking?'speaking':''}" src="assets/sofa-watercolour.webp" alt="Peep and Poppy sitting on the sofa with their feet hidden behind the coffee table">`:`<div class="actors" aria-label="Peep and Poppy together"><span class="actor peep ${speaking==='Peep'?'speaking':''}" role="img" aria-label="Peep"></span><span class="actor poppy ${speaking==='Poppy'?'speaking':''}" role="img" aria-label="Poppy"></span></div>`}${r.guest?`<img class="guest ${speaking==='Toby'?'speaking':''}" src="../cyber-detectives/assets/toby.png" alt="Toby has come over to ask for help">`:''}${p==='talk'?`<div class="conversation" aria-live="polite"><p class="scene-context">${esc(e.scene)}</p><span class="speaker">${speaking}</span><p>“${r.talk[game.line][1]}”</p><div class="conversation-bottom"><small>${game.line+1} of ${r.talk.length}</small><button class="primary" id="talk-next">${game.line===r.talk.length-1?'Look for clues':'Next'}</button></div></div>`:''}${p==='notification'?`<div class="notification"><span class="envelope" aria-hidden="true">✉</span><h2>${e.kind==='school'||e.kind==='website'?'Let’s check this website!':'Let’s check this message!'}</h2><p>${esc(e.title)}</p><button class="primary" id="open">Look at the clues</button></div>`:''}${p==='email'?`<section class="mail-panel" aria-label="Read and check the clues">${mailHTML(e)}<fieldset><legend>SCAM or SAFE?</legend><div class="answers"><button id="answer-scam" class="answer scam">SCAM</button><button id="answer-safe" class="answer safe">SAFE</button></div></fieldset><p id="retry" class="retry" role="status"></p></section>`:''}${p==='reward'?`<section class="reward-panel"><div class="reward-title"><span aria-hidden="true">★</span><div><p class="eyebrow">Well spotted!</p><h2 tabindex="-1">Safety Star ${game.stars} collected!</h2></div></div><p class="verdict">${e.answer==='scam'?'SCAM':'SAFE'} — ${e.answer==='scam'?'you spotted the trick!':'this looks safe in our story.'}</p>${e.reply.map(([name,line])=>`<p class="reply"><strong>${name}:</strong> ${line}</p>`).join('')}<div class="safety-tip"><h3>Our safety tip</h3>${e.tips.map(t=>`<p>${t}</p>`).join('')}${e.checks?`<ul>${e.checks.map(t=>`<li>${t}</li>`).join('')}</ul>`:''}${e.after?`<p>${e.after}</p>`:''}</div><button class="primary" id="next-case">${game.stars===8?'Collect our Cyber Smart Badge':game.round+1<r.cases.length?'Next level':'Next level'}</button></section>`:''}</div><div class="play-footer"><span>${p==='talk'?'Listen to our friends, then look for clues.':p==='notification'?'Take a closer look before you decide.':p==='email'?'STOP • THINK • CHECK — no need to rush.':'Smart choices make safer adventures.'}</span><span class="room-dots" aria-label="Eight levels">${rooms.map((_,i)=>`<i class="${i<=game.room?'visited':''}"></i>`).join('')}</span></div></section>`;
bind('talk-next',()=>{game.advanceTalk();play();if(game.phase==='notification')chime()});bind('open',()=>{game.openEmail();play();stage.querySelector('.mail-panel h2')?.setAttribute('tabindex','-1');stage.querySelector('.mail-panel h2')?.focus({preventScroll:true})});for(const answer of ['scam','safe'])bind('answer-'+answer,()=>{const result=game.answer(answer);if(result==='retry'){document.getElementById('retry').textContent='Good try! Look again: who sent it, where does the link lead, and are they asking for anything unusual?'}else if(result==='correct'){chime(true);play();stage.querySelector('.reward-title h2')?.focus({preventScroll:true})}});bind('next-case',()=>{game.next();game.phase==='finish'?go('finish'):play()})}
function finish(){music.victory(true);stage.innerHTML=`<section class="finish paper"><img src="assets/study-watercolour.webp" alt="Peep, Poppy and Professor Ollie celebrating in his study"><div class="finish-copy"><p class="eyebrow">Eight levels completed • Eight Safety Stars collected</p><h1 tabindex="-1">Cyber Smart Officers!</h1><div class="badge"><span aria-hidden="true">★</span><strong>CYBER SMART</strong><small>Scam Spotter</small></div>${stars()}<p>“You did it!” cheers Peep.</p><p>“You’re becoming a brilliant Scam Spotter!” says Poppy.</p><p>Professor Ollie smiles. “Always stop, think and check — and ask a trusted grown-up if you’re unsure.”</p><div class="golden-rule"><h2>Peep &amp; Poppy’s Golden Rule</h2><h3>STOP. THINK. CHECK.</h3><p>If something online doesn’t feel right, don’t click, don’t reply and don’t share anything until you’ve checked with a trusted grown-up.</p></div><button class="primary" id="replay">🏆 PLAY AGAIN</button><a class="secondary" href="../">Choose another game</a></div></section>`;bind('replay',()=>{game.reset();go('mission')})}
bind('back',()=>go(page==='mission'?'guidelines':'mission'));bind('sound',async()=>{if(!music.ctx||music.ctx.state!=='running'){music.enabled=true;await startMusic()}else {await music.toggle();musicLabel()}});
document.addEventListener('visibilitychange',()=>{if(document.hidden)music.pause();else music.resume();musicLabel()});

portrait.addEventListener('change',()=>{if(page==='ready'&&!needsRotation())go('play');else if(page==='play'||page==='ready')render()});
window.addEventListener('popstate',event=>{page=event.state?.page||'guidelines';render()});history.replaceState({page},'');render();
