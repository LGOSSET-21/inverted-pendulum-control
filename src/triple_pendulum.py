"""Three serial massless rods, point masses, absolute angles from upright.
State [x,v,theta1,omega1,theta2,omega2,theta3,omega3] in SI units.
"""
import numpy as np
from scipy.linalg import solve_continuous_are
from functools import lru_cache
from pendulum import rk4
N=3;L=np.full(N,.5/N);MASSES=np.full(N,.2/N)
W=np.cumsum(MASSES[::-1])[::-1];H=W*L
C=W[np.maximum.outer(np.arange(N),np.arange(N))]*L[:,None]*L[None,:]
Q=np.array([10.,1.,100.,1.,100.,1.,100.,1.]);R=.1

def mass_matrix(angles):
    M=np.zeros((N+1,N+1));M[0,0]=1.
    M[0,1:]=M[1:,0]=H*np.cos(angles)
    M[1:,1:]=C*np.cos(angles[:,None]-angles[None,:])
    return M

def dynamics(s,force):
    angles=s[2::2];omega=s[3::2]
    rhs=np.r_[force-.08*s[1]+np.sum(H*np.sin(angles)*omega**2),
              9.81*H*np.sin(angles)-np.sum(C*np.sin(angles[:,None]-angles[None,:])*omega[None,:]**2,axis=1)]
    result=np.empty(8);result[::2]=s[1::2];result[1::2]=np.linalg.solve(mass_matrix(angles),rhs)
    return result

def batch_dynamics(s,u):
    angles=s[:,2::2];omega=s[:,3::2];count=len(s)
    M=np.zeros((count,4,4));M[:,0,0]=1.
    M[:,0,1:]=M[:,1:,0]=H*np.cos(angles)
    delta=angles[:,:,None]-angles[:,None,:]
    M[:,1:,1:]=C*np.cos(delta)
    rhs=np.column_stack([u-.08*s[:,1]+np.sum(H*np.sin(angles)*omega**2,axis=1),9.81*H*np.sin(angles)-np.sum(C*np.sin(delta)*omega[:,None,:]**2,axis=2)])
    result=np.empty_like(s);result[:,::2]=s[:,1::2];result[:,1::2]=np.linalg.solve(M,rhs[:,:,None])[:,:,0]
    return result

def energy(s):
    return .5*s[1::2]@mass_matrix(s[2::2])@s[1::2]+9.81*np.sum(H*np.cos(s[2::2]))

def linear_model():
    force=np.zeros((4,8));force[0,1]=-.08
    for i in range(3):force[i+1,2+2*i]=9.81*H[i]
    A=np.zeros((8,8));A[range(0,8,2),range(1,8,2)]=1
    A[1::2]=np.linalg.solve(mass_matrix(np.zeros(3)),force)
    B=np.zeros((8,1));B[1::2,0]=np.linalg.solve(mass_matrix(np.zeros(3)),[1,0,0,0])
    return A,B

@lru_cache(maxsize=1)
def controller():
    A,B=linear_model();S=solve_continuous_are(A,B,np.diag(Q),np.array([[R]]));K=(B.T@S/R)[0]
    if np.linalg.eigvals(A-B@K[None,:]).real.max()>=0:raise ValueError('Unstable LQR')
    return K,S

def simulate(case='aligned',controlled=True,dt=.0025,duration=12.):
    angles={'aligned':(1,1,1),'opposed':(1,-1,1),'push':(0,0,0)}[case]
    s=np.zeros(8);s[2::2]=np.deg2rad(angles);K,_=controller();rows=[];status='completed'
    def force(t,state):return float(np.clip(-K@state,-8,8)) if controlled else 0.
    def disturbance(t):return 3. if case=='push' and 4<=t<4.2 else 0.
    for i in range(round(duration/dt)+1):
        t=i*dt;u=force(t,s);d=disturbance(t);rows.append([t,*s,u,d])
        if max(abs(s[2::2]))>np.deg2rad(60):status='tilt_limit';break
        if abs(s[0])>2:status='track_limit';break
        if i<round(duration/dt):s=rk4(s,t,dt,lambda tt,ss:dynamics(ss,force(tt,ss)+disturbance(tt)))
    data=np.array(rows)
    return data,metrics(data,status,4.2 if case=='push' else 0.)

def metrics(data,status,after=0.):
    within=(abs(data[:,1])<=.02)&(abs(data[:,2])<=.03)&(np.max(abs(data[:,[3,5,7]]),axis=1)<=np.deg2rad(1))&(np.max(abs(data[:,[4,6,8]]),axis=1)<=.05)
    bad=np.flatnonzero(~within|(data[:,0]<after));first=int(bad[-1]+1) if len(bad) else 0
    settle=float(data[first,0]) if status=='completed' and first<len(data) and data[-1,0]-data[first,0]>=1 else None
    return dict(status=status,end_s=float(data[-1,0]),settling_s=settle,peak_force_N=float(abs(data[:,9]).max()),effort_N2s=float(np.sum(np.diff(data[:,0])*(data[:-1,9]**2+data[1:,9]**2)/2)))

@lru_cache(maxsize=1)
def down_controller():
    """Cart-only LQR about the hanging equilibrium; angles remain absolute."""
    s=np.zeros(8);s[2::2]=np.pi;eps=1e-6
    A=np.column_stack([(dynamics(s+e*eps,0)-dynamics(s-e*eps,0))/(2*eps) for e in np.eye(8)])
    B=((dynamics(s,eps)-dynamics(s,-eps))/(2*eps))[:,None]
    S=solve_continuous_are(A,B,np.diag([20.,2.,10.,1.,10.,1.,10.,1.]),np.array([[.5]]))
    return (B.T@S/.5)[0],S
