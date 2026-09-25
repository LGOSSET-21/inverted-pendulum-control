const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const source=fs.readFileSync(path.resolve(__dirname,'../visualization/triple.html.in'),'utf8');
const sampling=source.match(/function sample\(rows,time\)\{[^\n]+/)[0];const c={};vm.createContext(c);vm.runInContext(sampling,c);
// Constant acceleration: q=t², dq/dt=2t. Interpolation must reproduce both.
const rows=[[0,0,0,0,0,0,0,0,0,0,0],[.02,.0004,.04,.0004,.04,.0004,.04,.0004,.04,1,0]];
assert.ok(Math.abs(c.sample(rows,.01)[1]-.0001)<1e-12,'Use endpoint velocities for physical interpolation');
assert.ok(Math.abs(c.sample(rows,.01)[2]-.02)<1e-12);
assert.equal(c.sample(rows,-1)[0],0);assert.equal(c.sample(rows,1)[0],.02);
console.log('Velocity-aware interpolation and time bounds passed.');

vm.runInContext(source.match(/function joints\(row\)\{[^\n]+/)[0],c);
const root=path.resolve(__dirname,'../results/triple');
const dataset=JSON.parse(fs.readFileSync(path.join(root,'experiments.json'),'utf8'));
for(const name of Object.keys(dataset.cases)){
 const saved=dataset.cases[name].lqr.data;
 const full=fs.readFileSync(path.join(root,name+'_lqr.csv'),'utf8').trim().split('\n').slice(1).map(line=>line.split(',').map(Number));
 for(let i=4;i<full.length;i+=8){const row=full[i],shown=c.sample(saved,row[0]);
  for(const k of [1,3,5,7])assert.ok(Math.abs(shown[k]-row[k])<.001,'Interpolation must match integrated motion');
  const points=c.joints(shown);for(let j=1;j<points.length;j++)assert.ok(Math.abs(Math.hypot(points[j][0]-points[j-1][0],points[j][1]-points[j-1][1])-1/6)<1e-12,'Rigid link length');
 }
}
console.log('Interpolated poses agree with full-resolution integration; all three links remain rigid.');
