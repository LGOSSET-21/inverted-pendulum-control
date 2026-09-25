import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import triple_pendulum as old
from massive_rods import Model
class MassiveRodTests(unittest.TestCase):
 def test_zero_rod_mass_recovers_original(self):
  m=Model(0);s=np.array([.1,.2,.3,-.2,-.1,.1,.2,-.3])
  np.testing.assert_allclose(m.mass_matrix(s[2::2]),old.mass_matrix(s[2::2]),atol=1e-15)
  np.testing.assert_allclose(m.dynamics(s,.7),old.dynamics(s,.7),atol=1e-10)
 def test_independent_rigid_body_energy(self):
  m=Model(.01);rng=np.random.default_rng(5)
  for _ in range(20):
   s=rng.normal(0,.3,8);v=np.array([s[1],0.]);pos=np.array([s[0],0.]);kin=.5*.8*s[1]**2;potential=0.
   for a,w,l,mp,mr in zip(s[2::2],s[3::2],m.L,m.points,m.rods):
    delta=l*np.array([np.sin(a),np.cos(a)]);dv=l*w*np.array([np.cos(a),-np.sin(a)])
    kin+=.5*mr*np.dot(v+dv/2,v+dv/2)+.5*(mr*l*l/12)*w*w
    potential+=mr*9.81*(pos+delta/2)[1]
    v+=dv;pos+=delta;kin+=.5*mp*np.dot(v,v);potential+=mp*9.81*pos[1]
   self.assertAlmostEqual(m.energy(s),kin+potential,places=12)
   grad=np.array([(m.energy(s+e*1e-6)-m.energy(s-e*1e-6))/2e-6 for e in np.eye(8)])
   self.assertAlmostEqual(grad@m.dynamics(s,.7),.7*s[1]-.08*s[1]**2,places=7)
   self.assertGreater(np.linalg.eigvalsh(m.mass_matrix(s[2::2])).min(),0)
 def test_linearisation_and_controller(self):
  m=Model(.01);A,B=m.linear_model();eps=1e-6
  num=np.column_stack([(m.dynamics(e*eps,0)-m.dynamics(-e*eps,0))/(2*eps) for e in np.eye(8)])
  np.testing.assert_allclose(A,num,atol=1e-6)
  np.testing.assert_allclose(B[:,0],(m.dynamics(np.zeros(8),eps)-m.dynamics(np.zeros(8),-eps))/(2*eps))
  K,P=m.controller();self.assertLess(np.linalg.eigvals(A-B@K[None,:]).real.max(),0)
  self.assertGreater(np.linalg.eigvalsh(P).min(),0)
 def test_recovery_and_refinement(self):
  m=Model(.01);a,ma=m.simulate('aligned');b,mb=m.simulate('aligned',dt=.00125)
  self.assertEqual(ma['status'],'completed');self.assertIsNotNone(ma['settling_s'])
  self.assertLessEqual(ma['peak_force_N'],8)
  np.testing.assert_allclose(a[:,1:9],b[::2,1:9],atol=2e-4)
