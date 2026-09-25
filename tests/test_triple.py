import unittest,importlib.util,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
class TripleTests(unittest.TestCase):
    def model(self):
        self.assertIsNotNone(importlib.util.find_spec('triple_pendulum'),'Triple model missing')
        import triple_pendulum as m
        return m
    def test_linearisation_and_control(self):
        m=self.model();A,B=m.linear_model();K,S=m.controller();eps=1e-6
        np.testing.assert_allclose(m.dynamics(np.zeros(8),0),0,atol=1e-12)
        J=np.column_stack([(m.dynamics(e*eps,0)-m.dynamics(-e*eps,0))/(2*eps) for e in np.eye(8)])
        np.testing.assert_allclose(J,A,atol=1e-6)
        self.assertLess(np.linalg.eigvals(A-B@K[None,:]).real.max(),0)
        np.testing.assert_allclose(A.T@S+S@A-S@B@B.T@S/m.R+np.diag(m.Q),0,atol=1e-5)
        self.assertGreater(np.linalg.eigvalsh(S).min(),0)
    def test_energy_power_balance(self):
        m=self.model();s=np.array([.1,.2,.2,-.1,-.1,.3,.15,-.2]);eps=1e-6
        grad=np.array([(m.energy(s+e*eps)-m.energy(s-e*eps))/(2*eps) for e in np.eye(8)])
        self.assertAlmostEqual(grad@m.dynamics(s,.7),.7*s[1]-.08*s[1]**2,places=7)
    def test_recovery_and_resolution(self):
        m=self.model();a,v=m.simulate('aligned');b,_=m.simulate('aligned',dt=.00125)
        self.assertEqual(v['status'],'completed');self.assertIsNotNone(v['settling_s'])
        self.assertLessEqual(v['peak_force_N'],8)
        np.testing.assert_allclose(a[:,1:9],b[::2,1:9],atol=.002)

    def test_batch_and_controllability(self):
        m=self.model();rng=np.random.default_rng(17);states=rng.normal(size=(25,8));forces=rng.uniform(-8,8,25)
        np.testing.assert_allclose(m.batch_dynamics(states,forces),np.array([m.dynamics(s,u) for s,u in zip(states,forces)]),atol=1e-10)
        A,B=m.linear_model();reach=np.column_stack([np.linalg.matrix_power(A,i)@B for i in range(8)])
        reach=reach/np.linalg.norm(reach,axis=0)
        self.assertEqual(np.linalg.matrix_rank(reach),8)

    def test_swingup_replay(self):
        root=Path(__file__).resolve().parents[1]
        self.assertTrue((root/'results/triple/swingup_lqr.csv').exists(),'Physical replay missing')
        rows=np.loadtxt(root/'results/triple/swingup_lqr.csv',skiprows=1,delimiter=',')
        np.testing.assert_allclose(rows[0,1:9],[0,0,np.pi,0,np.pi,0,np.pi,0],atol=1e-8)
        self.assertLessEqual(abs(rows[:,9]).max(),8.000001)
        self.assertLess(abs(rows[:,1]).max(),2)
        self.assertLess(abs(rows[-400:,1]).max(),.02)
        self.assertLess(abs(rows[-400:,[3,5,7]]).max(),np.deg2rad(1))
        self.assertLess(abs(rows[-400:,[2,4,6,8]]).max(),.05)
        from triple_swingup import simulate
        finer,metrics=simulate(dt=.00125)
        self.assertEqual(metrics['status'],'completed');self.assertIsNotNone(metrics['settling_s'])
        np.testing.assert_allclose(rows[:,1:9],finer[::2,1:9],atol=.01,rtol=.001)
