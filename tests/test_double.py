import importlib.util, sys, unittest
from pathlib import Path
from dataclasses import replace
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from pendulum import rk4

class DoubleTests(unittest.TestCase):
    def model(self):
        self.assertIsNotNone(importlib.util.find_spec('double_pendulum'), 'Double model missing')
        import double_pendulum
        return double_pendulum
    def test_linearisation_and_lqr(self):
        m=self.model(); A,B=m.linear_model(); K,S=m.controller(); eps=1e-6
        np.testing.assert_allclose(m.dynamics(np.zeros(6),0),0)
        numeric=np.column_stack([(m.dynamics(e*eps,0)-m.dynamics(-e*eps,0))/(2*eps) for e in np.eye(6)])
        np.testing.assert_allclose(A,numeric,atol=1e-7)
        np.testing.assert_allclose(B[:,0],m.dynamics(np.zeros(6),eps)/eps)
        self.assertEqual(np.linalg.matrix_rank(np.column_stack([np.linalg.matrix_power(A,i)@B for i in range(6)])),6)
        self.assertLess(np.linalg.eigvals(A-B@K[None,:]).real.max(),0)
        np.testing.assert_allclose(A.T@S+S@A-S@B@B.T@S/m.R+np.diag(m.Q),0,atol=1e-6)
    def test_energy(self):
        m=self.model();p=replace(m.P,friction=0);errors=[]
        for dt in [.001,.0005]:
            s=np.array([.1,.2,.2,-.1,-.15,.25]);E=m.energy(s,p)
            for i in range(round(1/dt)):s=rk4(s,i*dt,dt,lambda t,x:m.dynamics(x,0,p))
            errors.append(abs(m.energy(s,p)-E))
        self.assertLess(errors[1],1e-8)
        self.assertLess(errors[1],errors[0]*.2)
    def test_recovery_and_step_refinement(self):
        m=self.model()
        for case in ['aligned','opposed','push']:
            a,v=m.simulate(case);b,_=m.simulate(case,dt=.00125)
            self.assertEqual(v['status'],'completed');self.assertIsNotNone(v['settling_s'])
            self.assertLessEqual(v['peak_force_N'],8)
            np.testing.assert_allclose(a[-1,1:7],b[-1,1:7],atol=.002)
        a,v=m.simulate('push',controlled=False)
        self.assertGreater(v['end_s'],4)
        np.testing.assert_allclose(a[a[:,0]<4,1:7],0)
