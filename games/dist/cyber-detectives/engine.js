(function(root){
const levels=[
{room:'Living room',hero:'Toby',sprite:'toby',items:['book','toy'],intro:'Books and toys make a lovely pattern.'},
{room:'Conservatory',hero:'Toby',sprite:'toby',items:['terracotta plant','blue plant'],intro:'Look at the colours of the plant pots.'},
{room:'Bedroom',hero:'Finn',sprite:'flint',items:['shoes','hat'],intro:'Shoes and hats are ready for an adventure.'},
{room:'Garden',hero:'Finn',sprite:'flint',items:['yellow leaf','green leaf'],intro:'Yellow and green leaves take turns in the garden.'},
{room:'Kitchen',hero:'Milo',sprite:'milo',items:['cupcake','muffin'],intro:'A tasty-looking pattern! Look, then choose.'},
{room:'Detective’s study',hero:'Milo',sprite:'milo',items:['magnifying glass','key'],intro:'One last case in Uncle’s study.'}
];
class Adventure{constructor(){this.reset()}reset(){this.level=0;this.round=0;this.x=50;this.solved=levels.map(()=>[false,false]);this.medals=levels.map(()=>false);this.phase='intro';this.shuffle()}shuffle(){this.positions=[20+Math.random()*17,63+Math.random()*17];this.reverse=Math.random()<.5;this.x=[86,14,50][this.level%3]}get data(){return levels[this.level]}get sequence(){const a=this.data.items;return this.round===0?[a[0],a[1]]:[a[1],a[0]]}get answer(){return this.sequence[0]}get options(){const a=this.data.items;return this.reverse?[a[1],a[0]]:a.slice()}get nearest(){const p=this.positions;const i=Math.abs(this.x-p[0])<Math.abs(this.x-p[1])?0:1;return Math.abs(this.x-p[i])<=7?i:-1}start(){this.phase='play'}move(delta){if(this.phase==='play')this.x=Math.max(8,Math.min(92,this.x+delta))}choose(){if(this.phase!=='play')return 'blocked';const i=this.nearest;if(i<0)return 'far';if(this.options[i]!==this.answer)return 'wrong';this.solved[this.level][this.round]=true;this.phase='reward';if(this.round===1)this.medals[this.level]=true;return 'correct'}next(){if(this.phase!=='reward')return;if(this.round===0){this.round=1;this.shuffle();this.phase='play'}else if(this.level<5){this.level++;this.round=0;this.shuffle();this.phase='room'}else this.phase='final'}
}
root.Adventure=Adventure;root.ADVENTURE_LEVELS=levels;if(typeof module!=='undefined')module.exports={Adventure,levels};
})(typeof globalThis!=='undefined'?globalThis:this);
