"""Track a precomputed swing-up reference, then switch to upright LQR.
The feedforward trajectory is designed offline. Feedback is time-varying LQR,
not a claim of global stabilisation from arbitrary initial conditions.
"""
from pathlib import Path
from functools import lru_cache
import numpy as np
from scipy.interpolate import CubicHermiteSpline
from triple_pendulum import Q,R,metrics
from massive_rods import Model
model=Model(.01)
controller=model.controller
dynamics=model.dynamics
batch_dynamics=model.batch_dynamics
from pendulum import rk4
ROOT=Path(__file__).resolve().parents[1]

@lru_cache(maxsize=1)
def tracker():
    ref=np.load(ROOT/'results/massive_rods/swingup_reference.npz')
    T=float(ref['times'][-1])
    spline=CubicHermiteSpline(ref['times'],ref['states'],batch_dynamics(ref['states'],ref['forces']))
    times=np.linspace(0,T,round(T/.01)+1);dt=times[1];states=spline(times)
    forces=np.interp(times,ref['times'],ref['forces'])
    Ksteady,S=controller();gains=np.zeros((len(times),8));gains[-1]=Ksteady
    eps=1e-5
    for i in range(len(times)-2,-1,-1):
        s=states[i];u=forces[i]
        A=np.column_stack([(dynamics(s+e*eps,u)-dynamics(s-e*eps,u))/(2*eps) for e in np.eye(8)])
        B=((dynamics(s,u+eps)-dynamics(s,u-eps))/(2*eps))[:,None]
        Ad=np.eye(8)+A*dt+.5*A@A*dt**2;Bd=B*dt+.5*A@B*dt**2
        K=np.linalg.solve(np.array([[R*dt]])+Bd.T@S@Bd,Bd.T@S@Ad)
        S=np.diag(Q)*dt+Ad.T@S@Ad-Ad.T@S@Bd@K;S=(S+S.T)/2
        gains[i]=K[0]
    def command(t,s):
        if t>=T:return float(np.clip(-Ksteady@s,-8.,8.))
        refstate=spline(t);gain=np.array([np.interp(t,times,gains[:,j]) for j in range(8)])
        force=np.interp(t,ref['times'],ref['forces'])-gain@(s-refstate)
        return float(np.clip(force,-8.,8.))
    command.schedule = dict(times=times.tolist(), states=states.tolist(), gains=gains.tolist(), forces=forces.tolist())
    return command,T

def simulate(controlled=True,dt=.0025,duration=12.):
    command,T=tracker();s=np.array([0.,0.,np.pi,0.,np.pi,0.,np.pi,0.]);rows=[];status='completed'
    def force(t,s):return command(t,s) if controlled else 0.
    for i in range(round(duration/dt)+1):
        t=i*dt;u=force(t,s);rows.append([t,*s,u,0.])
        if abs(s[0])>2:status='track_limit';break
        if i<round(duration/dt):s=rk4(s,t,dt,lambda tt,ss:dynamics(ss,force(tt,ss)))
    data=np.array(rows)
    m=metrics(data,status,T);m['handoff_s']=T
    return data,m

def main():
    for key,enabled in [('lqr',True),('open',False)]:
        data,m=simulate(enabled)
        if enabled and (m['status']!='completed' or m['settling_s'] is None):raise RuntimeError(f'Swing-up not validated: {m}')
        np.savetxt(ROOT/f'results/massive_rods/swingup_{key}.csv',data,delimiter=',',header='time_s,x_m,v_m_s,theta1_rad,omega1_rad_s,theta2_rad,omega2_rad_s,theta3_rad,omega3_rad_s,force_N,push_N',comments='')
        print(key,m,'maximum cart displacement',abs(data[:,1]).max(),flush=True)
if __name__=='__main__':main()
