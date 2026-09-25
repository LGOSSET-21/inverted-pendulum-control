const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');const root=path.resolve(__dirname,'..');const {liveDerivative,liveStep}=require('../visualization/live-physics.js');const gain=JSON.parse(fs.readFileSync(path.join(root,'results/triple/experiments.json'),'utf8')).gain;
assert.deepEqual(liveDerivative(Array(8).fill(0),gain,null),Array(8).fill(0));
for(const point of [1,2,3]){let s=Array(8).fill(0);for(let i=0;i<6400;i++)s=liveStep(s,gain,i<160?{point,x:.008,y:point/6}:null,.00125);assert(Math.max(...s.map(Math.abs))<.01,'Recover after release at point '+point)}
console.log('Live nonlinear dynamics recover after gentle drag/release on all three points.');
