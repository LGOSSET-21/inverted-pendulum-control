const assert=require('node:assert/strict');
const {create,grab}=require('./helpers/massive_recovery.cjs');
// A strong sustained pull must overcome the local upright controller.
// Capping angle injections to a permanently safe envelope must fail this test.
for(const mass of [1,2,3]){
 const t=create();t.run(5);const e=grab(t,mass);
 t.cv.onpointermove({...e,clientX:e.clientX+180});
 let lost=false;
 for(let i=0;i<6400;i++){t.stepPhysics();if(t.phase==='down'){lost=true;break;}}
 assert.ok(lost,`mass ${mass}: a strong sustained pull never loses upright balance`);
 console.log(`PASS strong physical pull can topple mass ${mass}`);
}
function settled(t){assert.equal(t.phase,'balance');assert.ok(t.s.every((v,i)=>Math.abs([2,4,6].includes(i)?Math.atan2(Math.sin(v),Math.cos(v)):v)<.002),`residual ${t.s}`)}
for(const mass of [1,2,3])for(const dx of [-10,0,2,10]){
 const t=create();t.run(.1);const e=grab(t,mass);const before=t.s.slice();
 t.cv.onpointermove({...e,clientX:e.clientX+dx});assert.deepEqual(t.s,before,'input must not overwrite the physical state');
 for(let k=0;k<1600;k++){t.stepPhysics();assert.equal(t.phase,'balance',`small ${dx}px pull on mass ${mass} toppled`);}
 const releaseState=t.s.slice();t.cv.onpointerup(e);assert.deepEqual(t.s,releaseState,'release must not change position or velocity');t.run(15);settled(t);
 console.log(`PASS small ${dx}px pull, mass ${mass}: balance then settle`);
}
// Energy computed from individual bodies, independently of the mass matrix.
function energy(s){
 let x=s[0],y=0,vx=s[1],vy=0,E=.5*.8*vx*vx;
 for(let i=0;i<3;i++){
  const a=s[2+2*i],w=s[3+2*i],l=1/6,m=.2/3,r=.01;
  const dx=l*Math.sin(a),dy=l*Math.cos(a),dvx=l*Math.cos(a)*w,dvy=-l*Math.sin(a)*w;
  E+=.5*r*((vx+dvx/2)**2+(vy+dvy/2)**2)+.5*(r*l*l/12)*w*w+r*9.81*(y+dy/2);
  x+=dx;y+=dy;vx+=dvx;vy+=dvy;E+=.5*m*(vx*vx+vy*vy)+m*9.81*y;
 }
 return E;
}
for(const mass of [1,2,3]){
 const t=create(),s=[.1,.17,.3,-.4,-.2,.23,.4,-.19],F={point:mass,fx:.12,fy:-.07};
 const d=t.derivative(s,.31,F),eps=1e-6;
 const measured=(energy(s.map((x,i)=>x+eps*d[i]))-energy(s.map((x,i)=>x-eps*d[i])))/(2*eps);
 let vx=s[1],vy=0;for(let i=0;i<mass;i++){vx+=Math.cos(s[2+2*i])*s[3+2*i]/6;vy-=Math.sin(s[2+2*i])*s[3+2*i]/6;}
 const expected=.31*s[1]-.08*s[1]**2+F.fx*vx+F.fy*vy;
 assert.ok(Math.abs(measured-expected)<1e-8,`power mismatch ${measured} vs ${expected}`);
 console.log(`PASS mechanical power balance, mass ${mass}`);
}
// The open-loop upright system must fall naturally, without any mode threshold.
{
 const t=create();let s=[0,0,.01,0,.01,0,.01,0];
 for(let i=0;i<1600;i++)s=t.rk4(s,i*.00125,.00125,()=>0,null);
 assert.ok([2,4,6].some(i=>Math.abs(Math.atan2(Math.sin(s[i]),Math.cos(s[i])))>1));
 console.log('PASS no controller: gravity topples the upright system');
}
