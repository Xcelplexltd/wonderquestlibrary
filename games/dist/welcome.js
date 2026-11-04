(()=>{
const host=document.getElementById('safetyWelcome');
host.addEventListener('keydown',event=>event.stopPropagation());
const isBruno=location.pathname.includes('/bruno');
const hiddenRoots=[...document.body.children].filter(el=>el!==host&&!['SCRIPT','LINK'].includes(el.tagName));
hiddenRoots.forEach(el=>el.inert=true);
const title=isBruno?'Peep & Poppy’s Safety Promise':'Finn, Toby & Milo’s Careful Click Club';
const portrait=isBruno?'<img class="welcome-portrait" src="assets/finale.webp" alt="Peep and Poppy with Bruno">':'<div class="welcome-trio"><img src="assets/flint.png" alt="Finn the bunny"><img src="assets/toby.png" alt="Toby the fox"><img src="assets/milo.png" alt="Milo the mouse"></div>';
const rules=isBruno?[
['Keep passwords safe.','Never send your password to friends or strangers—even for a gift or help with a game.'],
['Pause before you tap.','Surprise prizes, free gifts and “hurry!” messages can be tricks. Ask a trusted grown-up before opening a link or pop-up.'],
['Check who is asking.','A familiar name does not prove a message is from your friend. If someone says “don’t tell,” tell a trusted grown-up.'],
['Keep your photos private.','Never send your photo to someone you do not know. Tell a trusted grown-up if someone asks.'],
['Ask before sharing.','Ask your friend and a trusted grown-up before sharing a photo. If your friend says no, keep it private. Check for addresses or other private details in the background.'],
['You can always ask for help.','If you are unsure—or have already tapped something—stop and tell a trusted grown-up. You are not in trouble for asking for help.']
]:[
['Look carefully.','Patterns repeat. In our game, look at the objects and notice which one comes next.'],
['Notice repeated warning signs.','If strange messages, pop-ups or requests keep coming back, stop and tell a trusted grown-up—even if you have told them before.'],
['Pause before clicking.','Seeing something again does not make it safe. Do not tap an unknown link or accept a surprise prize. Ask a trusted grown-up to check.'],
['Keep private things private.','Do not share passwords or personal photos with people online. If anything feels confusing, worrying or secret, speak to a trusted grown-up.']
];
const ruleIcons=isBruno?['🔒','✋','🔎','🖼️','🤝','💬']:['🔎','⚠️','✋','🔒'];
const nav=step=>'<div class="welcome-nav"><a href="../">‹ All games</a><span>'+step+' of 2 · Before we play</span></div>';
function safety(){host.innerHTML='<div class="welcome-shell">'+nav(1)+'<div class="welcome-heading">'+portrait+'<div><p class="welcome-kicker">STOP · THINK · ASK</p><h1 tabindex="-1">'+title+'</h1><p>'+ (isBruno?'Peep and Poppy have some friendly tips to help you stay safe online.':'Finn, Toby and Milo want you to look carefully and stay safe on the internet.')+'</p></div></div><ul class="safety-rules">'+rules.map((r,i)=>'<li><strong><span class="rule-icon" aria-hidden="true">'+ruleIcons[i]+'</span> '+r[0]+'</strong>'+r[1]+'</li>').join('')+'</ul><div class="welcome-bottom"><button class="welcome-button" id="welcomeNext">Next: our adventure →</button><p>Read together with a trusted grown-up.</p></div></div>';document.getElementById('welcomeNext').onclick=mission;requestAnimationFrame(()=>host.querySelector('h1').focus({preventScroll:true}));}
function mission(){host.scrollTop=0;host.innerHTML='<div class="welcome-shell">'+nav(2)+'<article class="welcome-mission"><img src="'+(isBruno?'assets/finale.webp':'assets/kitchen-finale.webp?v=7')+'" alt="'+(isBruno?'A birthday celebration with Peep, Poppy and Bruno':'Finn, Toby and Milo celebrating with Detective Uncle')+'"><h1 tabindex="-1">'+(isBruno?'A birthday mission for Bruno!':'Help our friends become cyber detectives!')+'</h1><p>'+(isBruno?'Now Peep and Poppy need your help to collect gifts for Bruno’s birthday! Explore the forest, find flowers and answer safety questions along the way.':'Now Finn, Toby and Milo need your help to become cyber detectives! Their detective uncle has hidden patterns in six cosy places. Solve the clues, collect medals and earn their badges together.')+'</p><button class="welcome-button" id="welcomeStart">Click to start game</button><small>Turn your phone sideways to play. Use the arrows to move and the hand to choose.</small></article></div>';document.getElementById('welcomeStart').onclick=()=>{hiddenRoots.forEach(el=>el.inert=false);host.hidden=true;document.getElementById('start').click();};host.querySelector('h1').focus({preventScroll:true});}
safety();
})();
