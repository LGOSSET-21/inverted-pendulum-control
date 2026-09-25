"""Uniform massive rigid rods plus retained endpoint masses; absolute SI angles."""
import numpy as np
from scipy.linalg import solve_continuous_are
from pendulum import rk4
from triple_pendulum import Q,R,metrics

class Model:
 def __init__(self,rod_mass=.01):
  if not np.isfinite(rod_mass) or rod_mass<0:raise ValueError('Invalid rod mass')
  self.L=np.full(3,1/6);self.points=np.full(3,.2/3);self.rods=np.full(3,rod_mass)
  downstream=np.cumsum(self.points[::-1])[::-1]+np.cumsum(self.rods[::-1])[::-1]-self.rods
  self.H=self.L*(downstream+self.rods/2)
  self.C=np.empty((3,3))
  for i in range(3):
   for j in range(3):
    self.C[i,j]=self.L[i]**2*(downstream[i]+self.rods[i]/3) if i==j else self.L[min(i,j)]*self.H[max(i,j)]
  self.total=.8+sum(self.points)+sum(self.rods)
 def mass_matrix(self,a):
  M=np.zeros((4,4));M[0,0]=self.total;M[0,1:]=M[1:,0]=self.H*np.cos(a)
  M[1:,1:]=self.C*np.cos(a[:,None]-a[None,:]);return M
 def dynamics(self,s,u):
  a=s[2::2];w=s[3::2]
  rhs=np.r_[u-.08*s[1]+sum(self.H*np.sin(a)*w*w),9.81*self.H*np.sin(a)-np.sum(self.C*np.sin(a[:,None]-a[None,:])*w[None,:]**2,axis=1)]
  d=np.empty(8);d[::2]=s[1::2];d[1::2]=np.linalg.solve(self.mass_matrix(a),rhs);return d
 def energy(self,s):return .5*s[1::2]@self.mass_matrix(s[2::2])@s[1::2]+9.81*np.sum(self.H*np.cos(s[2::2]))
 def linear_model(self):
  F=np.zeros((4,8));F[0,1]=-.08
  for i in range(3):F[i+1,2+2*i]=9.81*self.H[i]
  A=np.zeros((8,8));A[range(0,8,2),range(1,8,2)]=1;A[1::2]=np.linalg.solve(self.mass_matrix(np.zeros(3)),F)
  B=np.zeros((8,1));B[1::2,0]=np.linalg.solve(self.mass_matrix(np.zeros(3)),[1,0,0,0]);return A,B
 def controller(self):
  A,B=self.linear_model();P=solve_continuous_are(A,B,np.diag(Q),[[R]]);return (B.T@P/R)[0],P
 def simulate(self,case='aligned',dt=.0025,duration=12):
  s=np.zeros(8);s[2::2]=np.deg2rad({'aligned':[1,1,1],'opposed':[1,-1,1],'push':[0,0,0]}[case]);K,_=self.controller();rows=[];status='completed'
  for i in range(round(duration/dt)+1):
   t=round(i*dt,12);u=float(np.clip(-K@s,-8,8));push=3. if case=='push' and 4<=t<4.2 else 0.
   rows.append([t,*s,u,push])
   if not np.isfinite(s).all():raise ArithmeticError('Nonfinite state')
   if max(abs(s[2::2]))>np.deg2rad(60):status='tilt_limit';break
   if abs(s[0])>2:status='track_limit';break
   # Hold the external pulse on each interval, avoiding RK endpoint ambiguity.
   if i<round(duration/dt):s=rk4(s,t,dt,lambda tt,ss:self.dynamics(ss,float(np.clip(-K@ss,-8,8))+push))
  data=np.array(rows);return data,metrics(data,status,4.2 if case=='push' else 0)

 def batch_dynamics(self,s,u):
  a=s[:,2::2];w=s[:,3::2];count=len(s);M=np.zeros((count,4,4));M[:,0,0]=self.total
  M[:,0,1:]=M[:,1:,0]=self.H*np.cos(a);delta=a[:,:,None]-a[:,None,:];M[:,1:,1:]=self.C*np.cos(delta)
  rhs=np.column_stack([u-.08*s[:,1]+np.sum(self.H*np.sin(a)*w*w,axis=1),9.81*self.H*np.sin(a)-np.sum(self.C*np.sin(delta)*w[:,None,:]**2,axis=2)])
  d=np.empty_like(s);d[:,::2]=s[:,1::2];d[:,1::2]=np.linalg.solve(M,rhs[:,:,None])[:,:,0];return d
