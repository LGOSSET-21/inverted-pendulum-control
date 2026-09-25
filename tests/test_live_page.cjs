const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');const root=path.resolve(__dirname,'../visualization'),html=fs.readFileSync(path.join(root,'triple.html'),'utf8'),data=html.match(/<script id="data" type="application\/json">(.*?)<\/script>/s)[1];
let callback,clock=100;const els={};function el(id){return els[id]||(els[id]={clientWidth:420,width:0,height:0,textContent:id==='data'?data:'',getContext:()=>new Proxy({},{get:()=>()=>{},set:()=>true}),getBoundingClientRect:()=>({left:0,top:0,width:420,height:540}),setPointerCapture:()=>{}})}
const c={window:{devicePixelRatio:1},document:{getElementById:el,addEventListener:()=>{}},performance:{now:()=>clock},requestAnimationFrame:f=>{callback=f;return 1},cancelAnimationFrame:()=>{},ResizeObserver:class{observe(){}}};vm.createContext(c);vm.runInContext(fs.readFileSync(path.join(root,'live-physics.js'),'utf8'),c);vm.runInContext(fs.readFileSync(path.join(root,'live-interaction.js'),'utf8'),c);
const canvas=el('live-canvas'),event=(x,y)=>({clientX:x,clientY:y,pointerId:1,preventDefault(){}});
canvas.onpointerdown(event(210,225));assert(el('live-status').textContent.includes('Dragging'));
canvas.onpointermove(event(211.2,225));for(let i=0;i<12;i++){clock+=16.6667;callback(clock)}canvas.onpointerup();assert(el('live-status').textContent.includes('Released'));
for(let i=0;i<480;i++){clock+=16.6667;callback(clock)}assert(!el('live-status').textContent.includes('limit reached'));
el('live-reset').onclick();assert(el('live-status').textContent.includes('Grab'));
canvas.onpointerdown(event(210,250));canvas.onpointercancel();assert(!el('live-status').textContent.includes('Dragging'));
console.log('Pointer pick, drag, release, recovery, reset and cancellation passed.');
