const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync(__dirname+'/../visualization/massive-rods.html','utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
let frames=[],paint=0;const ctx=new Proxy({},{get:(_,key)=>key==='scale'?()=>{paint++}:()=>{},set:()=>true});
const elements={};for(const id of ['case','slider','time','point','massive','point-status','massive-status','play','restart','table'])elements[id]={value:id==='case'?'aligned':'0',clientWidth:500,textContent:'',innerHTML:'',getContext:()=>ctx};
const sandbox={document:{getElementById:id=>elements[id]},window:{addEventListener:()=>{}},devicePixelRatio:1,requestAnimationFrame:f=>frames.push(f),console};vm.createContext(sandbox);vm.runInContext(script,sandbox);assert(paint>=2);assert(elements.table.innerHTML.includes('massive')===false);assert(elements.table.innerHTML.includes('Massive'));
elements.play.onclick();frames.shift()(0);frames.shift()(1000);assert(elements.time.textContent.includes('0.05'));
for(const name of ['aligned','opposed','push']){elements.case.value=name;elements.case.onchange();elements.slider.value=12;elements.slider.oninput();assert(elements.time.textContent.includes('12.00'));}
elements.restart.onclick();assert(elements.time.textContent.includes('0.00'));console.log('Massive-rod page: drawing, playback, scenario changes, scrubbing and restart pass.');
