"""Two serial massless rods and point masses. Both angles are absolute from upright.
State: x, velocity, theta1, omega1, theta2, omega2 (SI units).
"""
from dataclasses import dataclass
import numpy as np
from pendulum import rk4

@dataclass(frozen=True)
class Parameters:
    cart: float = .8
    m1: float = .1
    m2: float = .1
    l1: float = .25
    l2: float = .25
    gravity: float = 9.81
    friction: float = .08
    force_limit: float = 8.

P=Parameters()
Q=np.array([10.,1.,100.,1.,100.,1.]);R=.1

def mass_matrix(a,b,p=P):
    h=(p.m1+p.m2)*p.l1; j=p.m2*p.l2; c=p.m2*p.l1*p.l2
    return np.array([[p.cart+p.m1+p.m2,h*np.cos(a),j*np.cos(b)],
                     [h*np.cos(a),h*p.l1,c*np.cos(a-b)],
                     [j*np.cos(b),c*np.cos(a-b),j*p.l2]])

def dynamics(s,force,p=P):
    _,v,a,wa,b,wb=s
    h=(p.m1+p.m2)*p.l1;j=p.m2*p.l2;c=p.m2*p.l1*p.l2
    rhs=np.array([force-p.friction*v+h*np.sin(a)*wa**2+j*np.sin(b)*wb**2,
                  h*p.gravity*np.sin(a)-c*np.sin(a-b)*wb**2,
                  j*p.gravity*np.sin(b)+c*np.sin(a-b)*wa**2])
    acc=np.linalg.solve(mass_matrix(a,b,p),rhs)
    return np.array([v,acc[0],wa,acc[1],wb,acc[2]])

def energy(s,p=P):
    _,v,a,wa,b,wb=s;vel=np.array([v,wa,wb])
    return .5*vel@mass_matrix(a,b,p)@vel+(p.m1+p.m2)*p.gravity*p.l1*np.cos(a)+p.m2*p.gravity*p.l2*np.cos(b)

def linear_model(p=P):
    mass=mass_matrix(0,0,p);force=np.zeros((3,6))
    force[0,1]=-p.friction
    force[1,2]=(p.m1+p.m2)*p.gravity*p.l1
    force[2,4]=p.m2*p.gravity*p.l2
    A=np.zeros((6,6));A[0,1]=A[2,3]=A[4,5]=1
    A[[1,3,5],:]=np.linalg.solve(mass,force)
    B=np.zeros((6,1));B[[1,3,5],0]=np.linalg.solve(mass,[1,0,0])
    return A,B

def controller(p=P):
    A,B=linear_model(p);H=np.block([[A,-B@B.T/R],[-np.diag(Q),-A.T]])
    values,V=np.linalg.eig(H);V=V[:,values.real < -1e-9]
    if V.shape[1]!=6:raise ValueError('No separated stable subspace')
    S=np.linalg.solve(V[:6].T,V[6:].T).T
    if abs(S.imag).max()>1e-6:raise ValueError('Complex Riccati solution')
    S=(S.real+S.real.T)/2;K=(B.T@S/R)[0]
    residual=A.T@S+S@A-S@B@B.T@S/R+np.diag(Q)
    if np.linalg.norm(residual)>1e-5 or np.linalg.eigvalsh(S).min()<=0 or np.linalg.eigvals(A-B@K[None,:]).real.max()>=0:
        raise ValueError('Invalid stabilising Riccati solution')
    return K,S

def simulate(case='aligned',controlled=True,dt=.0025,duration=12.,p=P):
    angles={'aligned':(3,3),'opposed':(3,-3),'push':(0,0)}[case]
    s=np.array([0.,0.,np.deg2rad(angles[0]),0.,np.deg2rad(angles[1]),0.]);K,_=controller(p)
    def inputs(t,state):
        u=float(np.clip(-K@state,-p.force_limit,p.force_limit)) if controlled else 0.
        return u,3. if case=='push' and 4<=t<4.2 else 0.
    rows=[];status='completed'
    for i in range(round(duration/dt)+1):
        t=i*dt;u,d=inputs(t,s);rows.append([t,*s,u,d])
        if max(abs(s[2]),abs(s[4]))>np.deg2rad(60):status='tilt_limit';break
        if abs(s[0])>2:status='track_limit';break
        if i<round(duration/dt):s=rk4(s,t,dt,lambda tt,ss:dynamics(ss,sum(inputs(tt,ss)),p))
    data=np.array(rows)
    within=(abs(data[:,1])<=.02)&(abs(data[:,2])<=.03)&(np.max(abs(data[:,[3,5]]),axis=1)<=np.deg2rad(1))&(np.max(abs(data[:,[4,6]]),axis=1)<=.05)
    bad=np.flatnonzero(~within | (data[:,0]<(4.2 if case=='push' else 0)))
    first=int(bad[-1]+1) if len(bad) else 0
    settling=float(data[first,0]) if status=='completed' and first<len(data) and data[-1,0]-data[first,0]>=1 else None
    return data,dict(status=status,end_s=float(data[-1,0]),settling_s=settling,peak_force_N=float(abs(data[:,7]).max()),effort_N2s=float(np.sum(np.diff(data[:,0])*(data[:-1,7]**2+data[1:,7]**2)/2)))
