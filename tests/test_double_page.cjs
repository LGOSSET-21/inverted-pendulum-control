// Exercise page handlers and drawing calls with an in-memory DOM/canvas stub.
// This checks JavaScript behaviour, not visual rendering in a browser.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(path.resolve(__dirname,'../visualization/double.html'),'utf8');
const data=html.match(/<script id="data" type="application\/json">(.*?)<\/script>/s)[1];
const script=html.match(/<script>(.*?)<\/script>/s)[1];
const elements={},counts={};
function element(id){if(!elements[id]){counts[id]=0;elements[id]={value:id==='case'?'swingup':'0',textContent:id==='data'?data:'',innerHTML:'',clientWidth:420,width:0,height:0,getContext:()=>new Proxy({},{get:()=>()=>{counts[id]++},set:()=>true})}}return elements[id]}
let frame;
const context={console,window:{devicePixelRatio:1},document:{getElementById:element,querySelector:()=>({}),addEventListener:()=>{}},performance:{now:()=>100},requestAnimationFrame:fn=>{frame=fn;return 1},cancelAnimationFrame:()=>{},matchMedia:()=>({addEventListener:()=>{}}),ResizeObserver:class{observe(){}},setTimeout:()=>1,clearTimeout:()=>{}};
vm.createContext(context);vm.runInContext(script,context);
assert(counts.open>0&&counts.lqr>0,'Both pendulums must be drawn on load');
assert(element('control-title').textContent.includes('swing-up'));
for(const name of ['swingup','aligned','opposed','push']){
 element('case').value=name;element('case').onchange();
 element('play').onclick();assert.doesNotThrow(()=>frame(99));
 assert.equal(element('time-label').textContent,'0.00 s');
 for(const t of ['0','4','5','12'])element('time').oninput({target:{value:t}});
 element('reset').onclick();assert.equal(element('time-label').textContent,'0.00 s');
}
console.log('All four scenario handlers, both canvas draws, first-frame timing and restart passed.');
