// Test animation helpers directly, without a browser or DOM.
const fs=require('node:fs'),assert=require('node:assert/strict'),vm=require('node:vm'),path=require('node:path');
const root=path.resolve(__dirname,'../visualization');
for(const name of ['double.html.in','demo.html.in','triple.html.in']){
 const source=fs.readFileSync(path.join(root,name),'utf8');
 const sampling=source.match(/function sample\(rows,time\)\{[^\n]+/)[0];
 const context={$:()=>({value:"1"})};vm.createContext(context);vm.runInContext(sampling,context);
 const rows=[[0,0,1],[.02,2,3],[.025,2.5,3.5]];
 assert.doesNotThrow(()=>context.sample(rows,-.001),name+': timestamps before first sample');
 assert.equal(context.sample(rows,-.001)[0],0);
 assert.equal(context.sample(rows,.025)[0],.025);
 assert.equal(context.sample(rows,20)[0],.025);
 assert.ok(Math.abs(context.sample(rows,.0225)[1]-2.25)<1e-10);
 // requestAnimationFrame can deliver a timestamp slightly before performance.now()
 const tick=source.match(/function tick\(now\)\{[^\n]+/)[0];
 vm.runInContext('let playing=true,t=0,last=100,raf=0,interactive=null;function playbackEnd(){return 12} function draw(){} function pause(){} function requestAnimationFrame(){return 1}',context);
 vm.runInContext(tick+';tick(99);',context);
 assert.equal(vm.runInContext('t',context),0,name+': clock must not run backwards');
}
console.log('Playback boundaries and first-frame timing passed for all three pages.');
