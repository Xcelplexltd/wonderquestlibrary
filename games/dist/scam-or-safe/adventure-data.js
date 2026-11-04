'use strict';
const rules = [
 ['🔐','Keep passwords private.','Never send your password in a message, even for a prize or help with a game.'],
 ['🎁','Be careful with unexpected prizes.','If you did not enter a competition, stop and check before believing you have won.'],
 ['🔗','Don’t click strange links.','Ask a trusted grown-up before opening an unexpected link.'],
 ['⏰','Don’t let urgent messages rush you.','Pause if a message tries to frighten you or says you must act NOW.'],
 ['👀','Check who really sent the message.','A familiar name can be copied. Check strange messages another way.'],
 ['🌐','Look carefully at website names.','Watch for strange spelling, extra letters and unexpected links.'],
 ['🧠','Even professional-looking messages can be fake.','A logo, good spelling or your first name does not prove a message is real.'],
 ['🙋','If you’re unsure — ask a trusted grown-up.','If something makes you worried or confused, stop and ask for help.']
];
const emails = [
 {title:'The Surprise Prize',kind:'prize',context:'Puzzle time',scene:'Peep is playing a puzzle game on a tablet. Suddenly a colourful message appears.',sender:'A surprise pop-up',message:'🎉 CONGRATULATIONS!\nYOU WON A BRAND-NEW TABLET!\nCLICK HERE TO CLAIM YOUR PRIZE NOW!',dialogue:[['Peep','Wow! I don’t remember entering a competition.'],['Poppy','Hmm… what do you think?']],answer:'scam',reply:[['Poppy','Correct! It could be a scam.'],['Peep','If you didn’t enter a competition, be suspicious of messages saying you’ve suddenly won a prize.']],tips:['Unexpected prizes can be tricks to make you click.','Never click the link. Ask a trusted grown-up first.']},
 {title:'The School Website',kind:'school',context:'Planning sports day',scene:'Poppy wants to check what time the school sports day begins. She opens the school website that her teacher has used before.',sender:'Our familiar school website',message:'Greenfield Primary School\nSports Day – Friday, 10:00 AM',note:'There are no strange pop-ups or requests for passwords.',dialogue:[['Poppy','I’ve visited this school website with my teacher before.']],answer:'safe',reply:[['Peep','That’s right! This looks safe.'],['Poppy','It is a website we already know and trust, and it isn’t asking me for anything unusual.']],tips:['Websites you already know can be safer than strange links sent in unexpected messages.']},
 {title:'The Free Game Coins',kind:'coins',context:'A message in a game',scene:'Peep receives a message while playing his favourite game.',sender:'A player Peep does not know',message:'Hey!\nWant 10,000 FREE game coins?\nSend me your username and password and I’ll add them to your account!',dialogue:[['Peep','10,000 coins sounds brilliant…'],['Poppy','But they want your password!']],answer:'scam',reply:[['Peep','You spotted it!'],['Poppy','Never share your password for prizes, coins, skins or anything else.']],tips:['🔐 Passwords are private.','Real games and trusted companies should not ask you to send someone your password in a message.']},
 {title:'A Message From Grandma',kind:'family',context:'Pancakes tomorrow',scene:'Poppy receives a message. She recognises Grandma’s usual contact, and the message doesn’t ask her to click anything or share personal information.',sender:'Grandma · her usual contact',message:'Hi Poppy!\nIt’s Grandma.\nI’m making pancakes tomorrow.\nWould you like strawberries on yours? ❤️',dialogue:[['Peep','Do you recognise who sent it?'],['Poppy','Yes. It’s Grandma’s normal contact.']],answer:'safe',reply:[['Peep','Correct!'],['Poppy','It’s from someone I know using the contact I normally use.']],tips:['Knowing who sent a message is an important clue.','But remember: if a message from someone you know suddenly seems strange, check with them another way.']},
 {title:'Is It Really Mum?',kind:'unknown',context:'An unknown number',scene:'Peep receives a message from a number he doesn’t recognise. He looks worried.',sender:'Unknown number',message:'Hi Peep. It’s Mum.\nMy phone broke so I’m using a new number.\nDon’t call me.\nI need you to send me the password for our shopping account quickly.',dialogue:[['Peep','It says it’s Mum…'],['Poppy','But how do we know?']],answer:'scam',reply:[['Poppy','Excellent spotting!'],['Peep','Someone can pretend to be a person we know.']],tips:['A familiar name doesn’t always mean a message is genuine.'],checks:['A new or unknown number','Requests for passwords','Messages telling you not to check','Pressure to act quickly'],after:'Ask a trusted grown-up and check with the real person another way.'},
 {title:'The Urgent Account Warning',kind:'urgent',context:'An alarming email',scene:'Poppy receives an email with a large red button.',sender:'Video account warning',message:'⚠️ URGENT!\nYour video account will be DELETED IN 10 MINUTES!\nClick below and enter your password immediately!',fakeButton:'SAVE MY ACCOUNT NOW',dialogue:[['Poppy','Oh no! Only ten minutes!'],['Peep','Wait. Why are they trying to rush you?']],answer:'scam',reply:[['Peep','Exactly!'],['Poppy','Scammers sometimes try to make people frightened or rushed so they click before thinking.']],tips:['STOP — THINK — CHECK','If a message says “NOW! QUICK! URGENT! YOUR ACCOUNT WILL CLOSE!”, don’t panic.','Don’t use the link in the message. Ask a trusted grown-up and check the account another way.']},
 {title:'The Almost-Right Website',kind:'website',context:'Look at every letter',scene:'Peep wants to visit www.happygames.com. But a message sends him to www.happygamess.com. The page looks almost exactly like the real Happy Games website.',sender:'Happy Games',expected:'www.happygames.com',actual:'www.happygamess.com',message:'Sign in with your username and password.',dialogue:[['Peep','It looks exactly like Happy Games!'],['Poppy','Look carefully at the website name.']],answer:'scam',reply:[['Poppy','Well spotted!'],['Peep','There is an extra S in the web address!']],tips:['Fake websites can look almost identical to real ones.'],checks:['🔍 The website name','🔍 Strange spelling','🔍 Extra letters','🔍 Unexpected links'],after:'When unsure, don’t sign in. Ask a trusted grown-up.'},
 {title:'The Tricky Final Challenge',kind:'polished',context:'Your final case',scene:'Poppy gets a message that looks as though it came from a game she really uses. It has the game’s correct logo, good spelling, Poppy’s first name and professional-looking pictures.',sender:'Happy Games · Account team',message:'Hi Poppy,\nWe noticed a problem with your account.\nPlease confirm your details.',link:'www.happygames-account.example/confirm',note:'Poppy notices the link leads to a different website name from the game’s normal website.',dialogue:[['Poppy','This one looks real.'],['Peep','Yes… but we weren’t expecting it.']],answer:'scam',reply:[['Peep','You solved the hardest challenge!'],['Poppy','Scams don’t always look silly. Some can look very convincing.']],tips:['Don’t decide something is safe just because it has a logo, your name or professional pictures.','When something unexpected asks you to:'],checks:['Click a link','Sign in','Share information','Send money','Act quickly'],after:'STOP — THINK — CHECK. Ask a trusted grown-up before doing anything.'}
];

const locations=[
 ['The living room','../cyber-detectives/assets/room-0.webp'],
 ['The classroom','assets/classroom.webp'],
 ['The living room','../cyber-detectives/assets/room-0.webp'],
 ['The kitchen','../cyber-detectives/assets/room-4.webp'],
 ['The playground','assets/playground.webp'],
 ['The classroom','assets/classroom.webp'],
 ['The library','assets/library.webp'],
 ['The playground','assets/playground.webp']
];
const rooms=emails.map((e,i)=>({name:e.title,location:locations[i][0],art:locations[i][1],cases:[i],sofa:i===0||i===2,talk:e.dialogue}));
class ScamAdventure {
 constructor(){this.reset()}
 reset(){this.room=0;this.round=0;this.line=0;this.stars=0;this.phase='talk';this.attempts=0}
 get place(){return rooms[this.room]}
 get email(){return emails[this.place.cases[this.round]]}
 get number(){return rooms.slice(0,this.room).reduce((n,r)=>n+r.cases.length,0)+this.round+1}
 advanceTalk(){if(this.phase!=='talk')return; if(this.line<this.place.talk.length-1)this.line++;else this.phase='notification'}
 openEmail(){if(this.phase==='notification')this.phase='email'}
 answer(value){if(this.phase!=='email')return 'blocked';if(value!==this.email.answer){this.attempts++;return 'retry'}this.stars++;this.phase='reward';return 'correct'}
 next(){if(this.phase!=='reward')return;if(this.round+1<this.place.cases.length){this.round++;this.phase='notification'}else if(this.room+1<rooms.length){this.room++;this.round=0;this.line=0;this.phase='talk'}else this.phase='finish'}
}
if(typeof module!=='undefined')module.exports={ScamAdventure,rooms,emails,rules};
