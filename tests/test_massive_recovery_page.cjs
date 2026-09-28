const assert=require('node:assert/strict'),{create,grab}=require('./helpers/massive_recovery.cjs');
function settled(t){assert.equal(t.phase,'balance');assert.ok(t.s.every((v,i)=>Math.abs(i===2||i===4||i===6?Math.atan2(Math.sin(v),Math.cos(v)):v)<.002),`residual ${t.s}`)}
for(const scenario of ['hanging','opposed','push']){const t=create();t.scenario.value=scenario;t.reset();const phases=new Set([t.phase]);for(let k=0;k<48000;k++){t.stepPhysics();phases.add(t.phase);}settled(t);if(scenario==='hanging')assert.deepEqual([...phases],['down','swing','balance']);console.log('PASS scenario',scenario,[...phases]);}
for(const mass of [1,2,3]){const t=create();t.run(5);for(let trial=0;trial<4;trial++){const e=grab(t,mass);for(let i=0;i<1200;i++){t.cv.onpointermove({...e,clientX:e.clientX+30*Math.sin(i/150)});t.stepPhysics();assert.equal(t.phase,'balance');}const before=t.s.slice();t.cv.onpointercancel(e);assert.deepEqual(t.s,before);assert.equal(t.drag,null);t.run(10);settled(t);}console.log('PASS repeated alternating gestures, cancel and recovery mass',mass);}
// A held stationary click must be dynamically identical to no click, even
// during the transient of a +1° initial perturbation.
for(const mass of [1,2,3]){const a=create(),b=create();a.run(.1);b.run(.1);grab(a,mass);a.run(3);b.run(3);assert.deepEqual(a.s,b.s);console.log('PASS zero-input click exact equivalence mass',mass);}
{
 const t=create();t.run(5);let e=grab(t,2);t.cv.onpointermove({...e,clientX:e.clientX+40});t.run(.15);
 t.cv.onpointerup({...e,pointerId:99});assert.ok(t.drag,'other pointer must not release');
 t.document.getElementById('pause').onclick();assert.equal(t.drag,null);const before=t.s.slice();grab(t,2);assert.equal(t.drag,null);assert.deepEqual(t.s,before);
 t.document.getElementById('pause').onclick();t.run(12);settled(t);
 e=grab(t,1);t.reset();assert.equal(t.drag,null);console.log('PASS pointer ownership, pause, resume and reset');
}
{
 const t=create();t.run(5);t.s[2]=1;const phases=new Set();for(let i=0;i<64000;i++){t.stepPhysics();phases.add(t.phase);}settled(t);assert.ok(phases.has('down')&&phases.has('swing'));console.log('PASS loss of upright → hanging → swing-up → balance');
}
{
 const t=create();t.run(22);assert.equal(t.history.length,1001);assert.equal(t.trail.length,65);
 assert.ok(Math.abs(t.history.at(-1).t-t.history[0].t-20)<1e-8);
 const row=t.history.at(-1);assert.equal(row.x,t.s[0]);for(let k=0;k<3;k++)assert.equal(row.angles[k],Math.atan2(Math.sin(t.s[2+2*k]),Math.cos(t.s[2+2*k]))*180/Math.PI);
 t.document.getElementById('pause').onclick();const frozen=JSON.stringify([t.history,t.trail,t.s]);t.paint();t.paint();assert.equal(JSON.stringify([t.history,t.trail,t.s]),frozen);
 t.reset();assert.equal(t.history.length,1);assert.equal(t.history[0].t,0);assert.equal(t.trail.length,1);
 console.log('PASS live chart data, 20-second history, frozen display and reset');
}
