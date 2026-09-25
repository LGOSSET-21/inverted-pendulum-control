"""Offline feasibility search for one triple-pendulum swing-up."""
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.sparse import lil_matrix
from triple_pendulum import batch_dynamics
ROOT=Path(__file__).resolve().parents[1]

def plan():
    N=81;T=6.;dt=T/(N-1);times=np.linspace(0,T,N);nx=8
    start=np.array([0,0,np.pi,0,np.pi,0,np.pi,0]);end=np.zeros(nx)
    z=times/T;states=(1-(3*z*z-2*z*z*z)[:,None])*start
    states[:,3::2]=(-np.pi*6*z*(1-z)/T)[:,None]
    states[:,0]=.5*np.sin(2*np.pi*z)*np.sin(np.pi*z)
    guess=np.column_stack([states,np.zeros(N)]).ravel();calls=[0]
    checkpoint=ROOT/'results/triple/swingup_attempt.npz'
    if checkpoint.exists():
        previous=np.load(checkpoint)
        if previous['states'].shape==(N,nx) and np.allclose(previous['times'],times):
            guess=np.column_stack([previous['states'],previous['forces']]).ravel()
            print('Resuming saved planning attempt',flush=True)
    def residual(flat):
        nodes=flat.reshape(N,nx+1);s=nodes[:,:nx];u=nodes[:,nx];f=batch_dynamics(s,u)
        mid=(s[:-1]+s[1:])/2+dt*(f[:-1]-f[1:])/8
        fm=batch_dynamics(mid,(u[:-1]+u[1:])/2)
        defect=(s[1:]-s[:-1])/dt-(f[:-1]+4*fm+f[1:])/6
        calls[0]+=1
        if calls[0]%2000==0:print('Evaluations',calls[0],'defect',np.max(abs(defect)),flush=True)
        return np.r_[defect.ravel(),(s[0]-start)*100,(s[-1]-end)*100,u*.0001]
    pattern=lil_matrix(((N-1)*nx+2*nx+N,N*(nx+1)),dtype=int)
    for i in range(N-1):pattern[i*nx:(i+1)*nx,i*(nx+1):(i+2)*(nx+1)]=1
    pattern[(N-1)*nx:N*nx,:nx]=1;pattern[N*nx:(N+1)*nx,-(nx+1):-1]=1
    for i in range(N):pattern[(N+1)*nx+i,i*(nx+1)+nx]=1
    lo=np.tile([-1.7,-12,-7,-30,-7,-30,-7,-35,-7.5],N)
    hi=-lo
    sol=least_squares(residual,guess,bounds=(lo,hi),jac_sparsity=pattern.tocsr(),max_nfev=600,tr_options={'maxiter':40},x_scale='jac',ftol=1e-10,xtol=1e-10,gtol=1e-9,verbose=1)
    defect=float(np.max(abs(residual(sol.x)[:(N-1)*nx])))
    out=ROOT/'results/triple';out.mkdir(exist_ok=True)
    np.savez(out/'swingup_attempt.npz',times=times,states=sol.x.reshape(N,nx+1)[:,:nx],forces=sol.x.reshape(N,nx+1)[:,nx],max_defect=defect)
    print('Max defect',defect,flush=True)
    if defect>.01:raise RuntimeError('Reference not sufficiently feasible; attempt retained, not published')
    np.savez(out/'swingup_reference.npz',times=times,states=sol.x.reshape(N,nx+1)[:,:nx],forces=sol.x.reshape(N,nx+1)[:,nx],max_defect=defect)
if __name__=='__main__':plan()
