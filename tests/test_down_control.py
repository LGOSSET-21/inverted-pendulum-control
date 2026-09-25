import unittest,sys,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import triple_pendulum as m
class DownControllerTests(unittest.TestCase):
    def test_equilibrium_riccati_and_export(self):
        s=np.zeros(8);s[2::2]=np.pi;eps=1e-6
        A=np.column_stack([(m.dynamics(s+e*eps,0)-m.dynamics(s-e*eps,0))/(2*eps) for e in np.eye(8)])
        B=((m.dynamics(s,eps)-m.dynamics(s,-eps))/(2*eps))[:,None];K,S=m.down_controller()
        self.assertLess(np.linalg.eigvals(A-B@K[None,:]).real.max(),0)
        np.testing.assert_allclose(A.T@S+S@A-S@B@B.T@S/.5+np.diag([20,2,10,1,10,1,10,1]),0,atol=1e-7)
        np.testing.assert_allclose(K,json.loads((ROOT/'results/triple/experiments.json').read_text())['downGain'])
