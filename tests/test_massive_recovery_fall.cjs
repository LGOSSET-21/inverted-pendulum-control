const assert=require('node:assert/strict'),{create,grab}=require('./helpers/massive_recovery.cjs');
for(const mass of [1,2,3]){
 const t=create();t.run(5);const e=grab(t,mass);t.cv.onpointermove({...e,clientX:e.clientX+180});
 let peak=0;for(let k=0;k<2400;k++){t.stepPhysics();peak=Math.max(peak,...[2,4,6].map(i=>Math.abs(Math.atan2(Math.sin(t.s[i]),Math.cos(t.s[i])))));}
 assert.ok(peak>Math.PI/2,`mass ${mass} must actually fall, peak ${peak}`);
 t.cv.onpointerup(e);const phases=new Set([t.phase]);
 for(let k=0;k<64000;k++){t.stepPhysics();phases.add(t.phase);assert.ok(t.s.every(Number.isFinite));}
 assert.ok(phases.has('down')&&phases.has('swing')&&phases.has('balance'));
 assert.equal(t.phase,'balance');assert.ok(t.s.every((v,i)=>Math.abs([2,4,6].includes(i)?Math.atan2(Math.sin(v),Math.cos(v)):v)<.002));
 console.log(`PASS mass ${mass}: real fall (peak ${(peak*180/Math.PI).toFixed(1)}°), release, down → swing → upright`);
}
