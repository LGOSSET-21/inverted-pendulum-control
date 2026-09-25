"""Offline trajectory design by Hermite-Simpson collocation.
This plans one manoeuvre, not a universal swing-up feedback controller.
"""
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.sparse import lil_matrix
import double_pendulum as model

ROOT=Path(__file__).resolve().parents[1]

def batch_dynamics(s,u):
    p=model.P;v=s[:,1];a=s[:,2];wa=s[:,3];b=s[:,4];wb=s[:,5]
    h=(p.m1+p.m2)*p.l1;j=p.m2*p.l2;c=p.m2*p.l1*p.l2
    mass=np.zeros((len(s),3,3));mass[:,0,0]=p.cart+p.m1+p.m2
    mass[:,0,1]=mass[:,1,0]=h*np.cos(a);mass[:,0,2]=mass[:,2,0]=j*np.cos(b)
    mass[:,1,1]=h*p.l1;mass[:,2,2]=j*p.l2;mass[:,1,2]=mass[:,2,1]=c*np.cos(a-b)
    rhs=np.column_stack([u-p.friction*v+h*np.sin(a)*wa**2+j*np.sin(b)*wb**2,h*p.gravity*np.sin(a)-c*np.sin(a-b)*wb**2,j*p.gravity*np.sin(b)+c*np.sin(a-b)*wa**2])
    acc=np.linalg.solve(mass,rhs[:,:,None])[:,:,0]
    return np.column_stack([v,acc[:,0],wa,acc[:,1],wb,acc[:,2]])

def plan():
    N=61;T=5.;dt=T/(N-1);times=np.linspace(0,T,N)
    start=np.array([0,0,np.pi,0,np.pi,0]);end=np.zeros(6)
    # Smooth reference guess, deliberately not presented as a simulated result.
    z=times/T;progress=3*z*z-2*z*z*z
    states=(1-progress[:,None])*start
    states[:,3]=states[:,5]=-np.pi*6*z*(1-z)/T
    states[:,0]=.5*np.sin(2*np.pi*z)*np.sin(np.pi*z)
    guess=np.column_stack([states,np.zeros(N)]).ravel()
    calls=[0]
    def residual(flat):
        nodes=flat.reshape(N,7);s=nodes[:,:6];u=nodes[:,6]
        f=batch_dynamics(s,u)
        mid=(s[:-1]+s[1:])/2+dt*(f[:-1]-f[1:])/8
        fm=batch_dynamics(mid,(u[:-1]+u[1:])/2)
        defect=(s[1:]-s[:-1])/dt-(f[:-1]+4*fm+f[1:])/6
        calls[0]+=1
        if calls[0]%1000==0:print('Evaluations',calls[0],'defect',np.max(abs(defect)),'endpoint',np.max(abs(s[-1])),flush=True)
        return np.r_[defect.ravel(),(s[0]-start)*100,(s[-1]-end)*100,u*.0001]
    pattern=lil_matrix(((N-1)*6+12+N,N*7),dtype=int)
    for i in range(N-1):pattern[i*6:(i+1)*6,i*7:(i+2)*7]=1
    pattern[(N-1)*6:(N-1)*6+6,:6]=1
    pattern[(N-1)*6+6:(N-1)*6+12,-7:-1]=1
    for i in range(N):pattern[(N-1)*6+12+i,i*7+6]=1
    lo=np.tile([-1.7,-12,-7,-25,-7,-30,-7.5],N)
    hi=np.tile([1.7,12,7,25,7,30,7.5],N)
    sol=least_squares(residual,guess,bounds=(lo,hi),jac_sparsity=pattern.tocsr(),max_nfev=400, tr_options={"maxiter":40}, x_scale="jac",ftol=1e-10,xtol=1e-10,gtol=1e-9,verbose=1)
    error=max(abs(residual(sol.x)[:(N-1)*6]))
    print('Max collocation derivative defect:',error,flush=True)
    if error>.01:raise RuntimeError('Trajectory has not converged sufficiently')
    out=ROOT/'results/double/swingup_reference.npz'
    np.savez(out,times=times,states=sol.x.reshape(N,7)[:,:6],forces=sol.x.reshape(N,7)[:,6],max_defect=error)
    print('Saved',out,flush=True)
if __name__=='__main__':plan()
