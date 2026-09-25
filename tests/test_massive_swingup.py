import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from massive_rods import Model
class MassiveSwingupTests(unittest.TestCase):
 def test_batch_matches_scalar(self):
  m=Model(.01);rng=np.random.default_rng(123);s=rng.normal(0,.5,(15,8));u=rng.uniform(-8,8,15)
  np.testing.assert_allclose(m.batch_dynamics(s,u),np.array([m.dynamics(x,f) for x,f in zip(s,u)]),atol=1e-10)
 def test_downward_equilibrium(self):
  m=Model(.01);s=np.zeros(8);s[2::2]=np.pi
  np.testing.assert_allclose(m.dynamics(s,0),0,atol=1e-10)
