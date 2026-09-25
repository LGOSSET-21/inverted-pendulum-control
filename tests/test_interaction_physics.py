"""Verify the browser solver against independent Python mass/Jacobian equations."""
import unittest,sys,json,subprocess,shutil
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import triple_pendulum as model
NODE=shutil.which('node')
if NODE is None:raise RuntimeError('Install Node.js and put node on PATH to run browser-physics tests.')
class InteractionPhysicsTests(unittest.TestCase):
    def test_mouse_force_jacobian_and_energy(self):
        rng=np.random.default_rng(71);K=model.controller()[0];cases=[]
        for point in [1,2,3]:
            for _ in range(8):
                s=rng.normal(0,.2,8);a=s[2::2];w=s[3::2];L=1/6
                J=np.zeros((2,4));J[0,0]=1
                J[0,1:point+1]=L*np.cos(a[:point]);J[1,1:point+1]=-L*np.sin(a[:point])
                pos=np.array([s[0]+L*np.sin(a[:point]).sum(),L*np.cos(a[:point]).sum()])
                target=pos+rng.normal(0,.04,2);force=3*(target-pos)-.025*(J@s[1::2]);force*=min(1,.12/max(np.linalg.norm(force),1e-12))
                u=float(np.clip(-K@s,-8,8));expected=model.dynamics(s,u);expected[1::2]+=np.linalg.solve(model.mass_matrix(a),J.T@force)
                eps=1e-6;gradient=np.array([(model.energy(s+e*eps)-model.energy(s-e*eps))/(2*eps) for e in np.eye(8)])
                power=u*s[1]-.08*s[1]**2+force@(J@s[1::2])
                cases.append(dict(s=s.tolist(),pull=dict(point=point,x=target[0],y=target[1]),expected=expected.tolist(),gradient=gradient.tolist(),power=power))
        js="""const fs=require('fs'),a=JSON.parse(fs.readFileSync(0,'utf8')),f=require('./visualization/live-physics.js').liveDerivative;for(const c of a.cases){const r=f(c.s,a.K,c.pull);if(r.some((v,i)=>Math.abs(v-c.expected[i])>1e-8))throw Error('Force transmission mismatch');if(Math.abs(r.reduce((v,x,i)=>v+x*c.gradient[i],0)-c.power)>1e-7)throw Error('Energy balance mismatch')}"""
        subprocess.run([NODE,'-e',js],cwd=ROOT,input=json.dumps(dict(K=K.tolist(),cases=cases)),text=True,check=True)
