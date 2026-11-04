'use strict';
// Each book supplies its own ordered image and narration paths.
const books = {
 'important-update': {title:'The Important Update',pages:Array.from({length:12},(_,i)=>{const n=String(i+1).padStart(2,'0');return {lesson:i===11,portrait:`assets/important-update/story_${n}.webp${n==='01'?'?v=20261024-wonderquest':''}`,landscape:`assets/important-update/story_${n}_landscape.webp${n==='01'?'?v=20261024-wonderquest':''}`,audio:`assets/important-update/audio/page${n}.mp3`};})},
 'mystery-download': {title:'The Mystery Download',pages:Array.from({length:13},(_,i)=>{const n=String(i+1).padStart(2,'0');return {lesson:i===12,portrait:`assets/mystery-download/story_${n}.webp${n==='04'?'?v=20261026-looked':n==='01'?'?v=20261024-wonderquest':''}`,landscape:`assets/mystery-download/story_${n}_landscape.webp${n==='01'?'?v=20261024-wonderquest':''}`,audio:`assets/mystery-download/audio/page${n}.mp3`};})},
 'mystery-wifi': {title:'The Mystery Wi-Fi',pages:Array.from({length:14},(_,i)=>{const n=String(i+1).padStart(2,'0');return {lesson:i===13,portrait:`assets/mystery-wifi/story_${n}.webp${n==='01'?'?v=20261024-wonderquest':''}`,landscape:`assets/mystery-wifi/story_${n}_landscape.webp${n==='01'?'?v=20261024-wonderquest':''}`,audio:`assets/mystery-wifi/audio/page${n}.mp3`};})},
 'pattern-puzzle': {title:'The Pattern Puzzle',pages:Array.from({length:11},(_,i)=>{const n=String(i+1).padStart(2,'0');return {lesson:i===10,portrait:`assets/pattern-puzzle/story_${n}.webp${n==='01'?'?v=20261024-wonderquest':''}`,landscape:`assets/pattern-puzzle/story_${n}_landscape.webp${n==='01'?'?v=20261024-wonderquest':''}`,audio:`assets/pattern-puzzle/audio/page${n}.mp3`};})},
 'tricky-message': {title:'The Tricky Message',pages:Array.from({length:14},(_,i)=>{const n=String(i+1).padStart(2,'0');return {lesson:i===13,portrait:`assets/tricky-message/story_${n}.webp${n==='01'?'?v=20261024-wonderquest':''}`,landscape:`assets/tricky-message/story_${n}_landscape.webp${n==='01'?'?v=20261024-wonderquest':''}`,audio:`assets/tricky-message/audio/page${n}.mp3`};})},
 'secret-code': {title:'The Secret Code',pages:Array.from({length:16},(_,i)=>{const n=String(i+1).padStart(2,'0');return {lesson:i===15,portrait:`assets/secret-code/story_${n}.webp${n==='01'?'?v=20261024-wonderquest':''}`,landscape:`assets/secret-code/story_${n}_landscape.webp${n==='01'?'?v=20261024-wonderquest':''}`,audio:`assets/secret-code/audio/page${n}.mp3`};})},
 'little-ai-helper': {title:'The Little AI Helper',pages:Array.from({length:14},(_,i)=>{const n=String(i+1).padStart(2,'0');return {lesson:i===13,portrait:`assets/little-ai-helper/story_${n}.webp${n==='01'?'?v=20261024-wonderquest':''}`,landscape:`assets/little-ai-helper/story_${n}_landscape.webp${n==='01'?'?v=20261024-wonderquest':''}`,audio:`assets/little-ai-helper/audio/page${n}.mp3`};})},
 'magic-picture': {title:'The Magic Picture',pages:[1,3,4,5,6,7,8,9,10,11,12,13].map(sourcePage=>{const n=String(sourcePage).padStart(2,'0');return {lesson:sourcePage===13,portrait:`assets/watercolour/story_${n}.webp${n==='01'?'?v=20261024-wonderquest':''}`,landscape:`assets/watercolour/story_${n}_landscape.webp${n==='01'?'?v=20261024-wonderquest':''}`,audio:`assets/audio/page${n}.mp3`};})}
};
const id=new URLSearchParams(location.search).get('book')||'magic-picture';
const book=books[id];
if(!book){document.getElementById('reader').innerHTML='<p style="text-align:center;padding:50px">This book is not on our shelf yet. <a href="../stories.html">Back to the bookshelf</a></p>';document.getElementById('title').textContent='Book not found';document.getElementById('bookmark').hidden=true;}
else {
 const $=s=>document.getElementById(s), audio=$('audio'), image=$('page');
 const key=`getsetgo.${id}.watercolour-v2`;
 const read=s=>{try{return localStorage.getItem(`${key}.${s}`)}catch{return null}};
 const save=(s,v)=>{try{v===null?localStorage.removeItem(`${key}.${s}`):localStorage.setItem(`${key}.${s}`,String(v))}catch{}};
 const valid=v=>v!==null&&/^\d+$/.test(v)&&Number(v)<book.pages.length;
 let page=valid(read('page'))?Number(read('page')):0;
 let bookmark=valid(read('bookmark'))?Number(read('bookmark')):null;
 let request=0,loading=false;
 $('title').textContent=book.title;document.title=`${book.title} — Wonder Quest Reader`;
 function buttons(){ $('play').textContent=loading?'Loading…':audio.paused?'♫ Read to Me':'■ Stop reading';$('play').disabled=loading;$('play').hidden=!book.pages[page].audio; }
 function stop(){request++;audio.pause();audio.removeAttribute('src');audio.load();loading=false;buttons();}
 function selectImage(){const landscape=$('stage').clientWidth>$('stage').clientHeight;const src=book.pages[page][landscape?'landscape':'portrait']+'?v=20261023-series-footer';if(image.getAttribute('src')!==src){$('imageError').hidden=true;image.hidden=false;image.src=src;} }
 function render(){const p=book.pages[page];buttons();$('reader').classList.toggle('lesson-page',Boolean(p.lesson));image.alt=`${book.title}, page ${page+1}. ${p.audio?"Use Read to Me for narration.":""}`;selectImage();$('pageLabel').textContent=`Page ${page+1} of ${book.pages.length}`;$('prev').disabled=page===0;$('next').disabled=page===book.pages.length-1;$('restart').disabled=page===0;$('bookmark').setAttribute('aria-pressed',String(bookmark===page));$('bookmark').querySelector('span').textContent=bookmark===page?'Bookmarked':'Bookmark';$('bookmark').setAttribute('aria-label',bookmark===page?'Remove bookmark from this page':'Bookmark this page');$('bookmark').title=bookmark===page?'Remove bookmark from this page':'Bookmark this page';$('saved').hidden=bookmark===null;$('hint').textContent=page===book.pages.length-1?'The end · What did you discover?':'Read at your own pace · Use the arrows to turn the page';save('page',page);}
 function turn(n){if(n<0||n>=book.pages.length)return;stop();page=n;$('status').textContent='';render();}
 $('prev').onclick=()=>turn(page-1);$('next').onclick=()=>turn(page+1);$('restart').onclick=()=>turn(0);
 $('bookmark').onclick=()=>{bookmark=bookmark===page?null:page;save('bookmark',bookmark);render();};$('saved').onclick=()=>{if(bookmark!==null)turn(bookmark)};
 $('play').onclick=async()=>{if(loading||!book.pages[page].audio)return;if(!audio.paused){stop();return;}const token=++request;loading=true;buttons();$('status').textContent='';audio.src=book.pages[page].audio;const timer=setTimeout(()=>{if(token===request&&loading){stop();$('status').textContent='Narration is taking a little longer. Please try again.'}},20000);try{await audio.play();}catch{if(token===request)$('status').textContent='The narration could not play. Please try again.';}finally{clearTimeout(timer);if(token===request){loading=false;buttons();}}};
 for(const event of ['play','pause','ended'])audio.addEventListener(event,buttons);
 audio.addEventListener('error',()=>{if(audio.getAttribute('src')){loading=false;$('status').textContent='The narration could not load. Please try again.';buttons();}});
 image.onerror=()=>{image.hidden=true;$('imageError').hidden=false;};
 window.addEventListener('resize',selectImage);
 window.addEventListener('pagehide',stop);
 document.addEventListener('keydown',e=>{if(e.altKey||e.ctrlKey||e.metaKey||e.target.matches('input,textarea,select'))return;if(e.key==='ArrowRight'){e.preventDefault();turn(page+1)}if(e.key==='ArrowLeft'){e.preventDefault();turn(page-1)}});
 render();
}
