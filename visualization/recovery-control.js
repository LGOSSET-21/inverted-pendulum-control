/* Hybrid cart-only recovery. No state resets, no joint motors. */
class RecoveryControl {
 constructor(D,scenario,time){this.D=D;this.mode=scenario==='swingup'&&time<6?'tracking':'balance';this.referenceTime=time;this.low=0;this.ready=0;this.attempts=0;this.scenario=scenario;this.time=time;}
 feedback(s){const tracking=this.mode==='tracking'||this.mode==='reswing';return liveFeedback(s,this.D.gain,tracking?this.D.tracking:null,this.referenceTime)}
 downError(s){const e=s.slice();for(const k of [2,4,6])e[k]=Math.atan2(Math.sin(s[k]-Math.PI),Math.cos(s[k]-Math.PI));return e}
 update(s,pull,dt){this.time+=dt;const tracking=this.mode==='tracking'||this.mode==='reswing';if(tracking){this.referenceTime+=dt;if(this.referenceTime>=6)this.mode='balance'}
  if(this.mode==='balance'||this.mode==='tracking'||this.mode==='reswing'){if(this.feedback(s).authority<.1)this.low+=dt;else this.low=0;if(this.low>.15){this.mode='damping';this.low=0;this.ready=0}}
  if(this.mode==='damping'){const e=this.downError(s),near=Math.abs(e[0])<.005&&Math.abs(e[1])<.015&&[2,4,6].every(k=>Math.abs(e[k])<.003&&Math.abs(e[k+1])<.015);this.ready=!pull&&near?this.ready+dt:0;if(this.ready>.25){this.mode='reswing';this.referenceTime=0;this.ready=0;this.attempts++}}
 }
 force(s){if(this.mode!=='damping')return this.feedback(s).force;const e=this.downError(s),angle=Math.max(...[2,4,6].map(k=>Math.abs(e[k]))),speed=Math.max(...[3,5,7].map(k=>Math.abs(e[k])));const a=Math.max(0,Math.min(1,(1.5-angle)/.5))*Math.max(0,Math.min(1,(8-speed)/3));const down=Math.max(-8,Math.min(8,-this.D.downGain.reduce((v,k,i)=>v+k*e[i],0))),brake=Math.max(-2,Math.min(2,-1.5*s[1]-2*s[0]));return a*down+(1-a)*brake}
 step(s,pull,dt){this.update(s,pull,dt);const extra=this.scenario==='push'&&this.time>=4&&this.time<4.2?3:0,rhs=v=>liveDerivative(v,this.D.gain,pull,this.force(v)+extra),add=(v,k)=>s.map((x,i)=>x+k*v[i]),a=rhs(s),b=rhs(add(a,dt/2)),c=rhs(add(b,dt/2)),d=rhs(add(c,dt));return s.map((x,i)=>x+dt*(a[i]+2*b[i]+2*c[i]+d[i])/6)}
 label(){return this.mode==='damping'?'Recovery: damping toward the hanging equilibrium':this.mode==='reswing'?'Recovery: raising the pendulum again':this.mode==='tracking'?'Tracking the swing-up':'Balancing upright'}
}
if(typeof module!=='undefined')module.exports={RecoveryControl};
