import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import pendulum as model

class LQRTests(unittest.TestCase):
    def test_riccati_and_stability(self):
        self.assertTrue(hasattr(model, 'lqr_controller'), 'LQR solver is missing')
        A,B=model.linear_model()
        for name in ['gentle','responsive']:
            K,S=model.lqr_controller(name)
            Q,R=model.LQR_WEIGHTS[name]
            residual=A.T@S+S@A-S@B@B.T@S/R+np.diag(Q)
            np.testing.assert_allclose(residual,0,atol=1e-7)
            self.assertGreater(np.linalg.eigvalsh(S).min(),0)
            self.assertLess(np.linalg.eigvals(A-B@K[None,:]).real.max(),0)
            np.testing.assert_allclose(K,(B.T@S/R)[0])
    def test_nonlinear_recovery_and_effort(self):
        self.assertTrue(hasattr(model, 'lqr_controller'), 'LQR solver is missing')
        for name in ['gentle','responsive']:
            for task,tilt in [('balance',10),('position',5),('push',0)]:
                a,m=model.simulate(tilt,task,method=name)
                b,_=model.simulate(tilt,task,method=name,dt=.0025)
                self.assertEqual(m['status'],'completed')
                self.assertIsNotNone(m['settling_time_s'])
                self.assertLessEqual(m['peak_force_N'],model.P.force_limit)
                np.testing.assert_allclose(a[-1,1:5],b[-1,1:5],atol=2e-3)
                expected=np.sum(np.diff(a[:,0])*(a[1:,5]**2+a[:-1,5]**2)/2)
                self.assertAlmostEqual(m['force_squared_integral_N2s'],expected)
