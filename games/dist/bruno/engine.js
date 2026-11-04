'use strict';
const rewards=[{name:'Candies',icon:'🍬'},{name:'Chocolates',icon:'🍫'},{name:'Cap',icon:'🧢'},{name:'Book for Bruno',icon:'📕'},{name:'Honey',icon:'🍯'},{name:'Pancakes',icon:'🥞'}];
const forests=[{name:'Bluebell Wood',image:'forest1-clear.webp'},{name:'Lakeside Trail',image:'forest2-clear.webp'},{name:'Bluebell & Tulip Fields',image:'forest3-clear.webp'},{name:'Rolling Hills',image:'forest4-clear.webp'},{name:'Stream & Bridges',image:'forest5-clear.webp'},{name:'Bruno’s Village',image:'forest6-clear.webp'}];
const WORLD_END=3500,CHEST_X=3240,WALK_SPEED=145;
class BirthdayAdventure{
 constructor(){this.reset();}
 reset(){this.level=0;this.phase='intro';this.bells=0;this.tulips=0;this.gifts=[];this.used=new Set();this.skills=Object.fromEntries(Object.keys(topics).map(k=>[k,{seen:0,correct:0,misses:0}]));this.prepareTrail();}
 prepareTrail(){this.x=100;this.direction=1;this.distance=0;this.question=null;this.attempts=0;this.solved=false;this.boxes=[440,980,1520,2100,2680].map((x,i)=>({x,kind:(i+this.level)%2?'tulips':'bells',place:i%2?'bench':'rock',collected:false}));}
 start(){if(this.phase!=='intro')return false;this.phase='level';return true;}
 enter(){if(this.phase!=='level')return false;this.phase='play';return true;}
 move(direction,seconds){if(this.phase!=='play'||this.solved||![-1,1].includes(direction)||!Number.isFinite(seconds)||seconds<0)return false;const old=this.x;this.x=Math.max(70,Math.min(CHEST_X-115,this.x+direction*WALK_SPEED*Math.min(seconds,.1)));this.direction=direction;this.distance+=Math.abs(this.x-old);return old!==this.x;}
 get found(){return this.boxes.filter(b=>b.collected).length;}
 get nearBox(){return this.boxes.find(b=>!b.collected&&Math.abs(this.x-b.x)<135);}
 get atChest(){return Math.abs(this.x-(CHEST_X-115))<95;}
 collect(){if(this.phase!=='play'||this.solved)return null;const box=this.nearBox;if(!box)return null;box.collected=true;if(box.kind==='bells')this.bells+=3;else this.tulips+=3;return box;}
 selectQuestion(){if(this.phase!=='play'||this.found!==5||!this.atChest)return null;if(this.question){this.phase='quiz';return this.question;}const keys=Object.keys(topics),s=this.skills;let topic=keys.find(k=>!s[k].seen);if(!topic)topic=keys.filter(k=>bank.some((q,i)=>q.topic===k&&!this.used.has(i))).sort((a,b)=>(s[b].misses*3-s[b].seen)-(s[a].misses*3-s[a].seen))[0];const target=s[topic].misses?0:Math.min(1,s[topic].correct);const chosen=bank.map((q,i)=>({q,i})).filter(x=>x.q.topic===topic&&!this.used.has(x.i)).sort((a,b)=>Math.abs(a.q.level-target)-Math.abs(b.q.level-target))[0];this.used.add(chosen.i);this.question=chosen.q;this.phase='quiz';return this.question;}
 closeQuestion(){if(this.phase==='quiz')this.phase='play';}
 answer(i){if(this.phase!=='quiz'||!this.question||this.solved||!Number.isInteger(i)||i<0||i>2)return null;this.attempts++;const good=i===this.question.ok,s=this.skills[this.question.topic];if(this.attempts===1){s.seen++;good?s.correct++:s.misses++;}if(good){this.solved=true;this.gifts.push(rewards[this.level]);this.phase='complete';}return good;}
 next(){if(this.phase!=='complete')return false;if(this.level===5){this.phase='finale';return true;}this.level++;this.prepareTrail();this.phase='level';return true;}
}
