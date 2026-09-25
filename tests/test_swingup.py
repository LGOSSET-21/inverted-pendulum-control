import unittest,json
from pathlib import Path
import numpy as np
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))

class SwingupTests(unittest.TestCase):
    def test_physical_swingup_trajectory(self):
        root=Path(__file__).resolve().parents[1]
        path=root/'results/double/swingup_lqr.csv'
        self.assertTrue(path.exists(),'Verified swing-up trajectory is missing')
        rows=np.loadtxt(path,delimiter=',',skiprows=1)
        np.testing.assert_allclose(rows[0,1:7],[0,0,np.pi,0,np.pi,0],atol=1e-8)
        self.assertLess(np.max(abs(rows[:,7])),8.000001)
        self.assertLess(np.max(abs(rows[:,1])),2)
        self.assertLess(np.max(abs(rows[-400:,3])),np.deg2rad(1))
        self.assertLess(np.max(abs(rows[-400:,5])),np.deg2rad(1))
        self.assertLess(np.max(abs(rows[-400:,1])),.02)
        self.assertLess(np.max(abs(rows[-400:,[2,4,6]])),.05)

    def test_vectorised_planning_model(self):
        from plan_swingup import batch_dynamics
        from double_pendulum import dynamics
        rng=np.random.default_rng(42);states=rng.normal(size=(30,6));forces=rng.uniform(-8,8,30)
        np.testing.assert_allclose(batch_dynamics(states,forces),np.array([dynamics(s,u) for s,u in zip(states,forces)]),atol=1e-10)

    def test_replay_and_step_refinement(self):
        from swingup import simulate
        a,m=simulate(dt=.0025);b,n=simulate(dt=.00125)
        self.assertEqual(m['status'],'completed');self.assertIsNotNone(m['settling_s'])
        self.assertEqual(n['status'],'completed');self.assertIsNotNone(n['settling_s'])
        # Compare all states over the entire manoeuvre, not just the final equilibrium.
        np.testing.assert_allclose(a[:,1:7],b[::2,1:7],atol=.01,rtol=.001)
