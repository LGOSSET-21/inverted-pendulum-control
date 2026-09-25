import sys,unittest
from pathlib import Path
from dataclasses import replace
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from pendulum import *

class PhysicsTests(unittest.TestCase):
    def test_equilibrium_and_linearisation(self):
        np.testing.assert_allclose(dynamics(np.zeros(4),0),0)
        A,B=linear_model();eps=1e-6
        numeric=np.column_stack([(dynamics(np.eye(4)[i]*eps,0)-dynamics(-np.eye(4)[i]*eps,0))/(2*eps) for i in range(4)])
        np.testing.assert_allclose(numeric,A,atol=1e-8)
        np.testing.assert_allclose((dynamics(np.zeros(4),eps)-dynamics(np.zeros(4),-eps))/(2*eps),B[:,0])
    def test_poles(self):
        A,B=linear_model();K=controller()
        self.assertGreater(np.max(np.linalg.eigvals(A).real),0)
        np.testing.assert_allclose(np.sort(np.linalg.eigvals(A-B@K[None,:])),np.sort(POLES),atol=1e-8)
    def test_energy_without_friction(self):
        p=replace(P,cart_friction=0);s=np.array([0.,.2,.2,.1]);start=energy(s,p)
        for i in range(1000):s=rk4(s,i*.001,.001,lambda t,x:dynamics(x,0,p))
        self.assertLess(abs(energy(s,p)-start),1e-8)
    def test_recovery_saturation_and_resolution(self):
        for task in ['balance','position','push']:
            a,m=simulate(5,task);b,_=simulate(5,task,dt=.0025)
            self.assertEqual(m['status'],'completed');self.assertIsNotNone(m['settling_time_s'])
            self.assertLess(abs(m['final_angle_deg']),.1)
            self.assertLessEqual(m['peak_force_N'],P.force_limit)
            np.testing.assert_allclose(a[-1,1:5],b[-1,1:5],atol=2e-3)
        _,m=simulate(5,controlled=False);self.assertEqual(m['status'],'tilt_limit')
if __name__=='__main__':unittest.main()
