"""Point-mass cart-pole. Angle zero is upright, positive toward the right."""
from dataclasses import dataclass,asdict
import numpy as np

@dataclass(frozen=True)
class Parameters:
    cart_mass: float = .8
    bob_mass: float = .2
    length: float = .5
    gravity: float = 9.81
    cart_friction: float = .08
    force_limit: float = 8.

P=Parameters()
POLES=np.array([-1.4,-1.8,-2.2,-2.6])

def dynamics(state,force,p=P):
    """State = cart position, cart velocity, angle [rad], angular velocity."""
    x,v,theta,omega=state
    s,c=np.sin(theta),np.cos(theta)
    accel=(force-p.cart_friction*v+p.bob_mass*p.length*omega**2*s-p.bob_mass*p.gravity*s*c)/(p.cart_mass+p.bob_mass*s*s)
    angular=(p.gravity*s-accel*c)/p.length
    return np.array([v,accel,omega,angular])

def linear_model(p=P):
    M,m,l,g,b=p.cart_mass,p.bob_mass,p.length,p.gravity,p.cart_friction
    A=np.array([[0,1,0,0],[0,-b/M,-m*g/M,0],[0,0,0,1],[0,b/(M*l),(M+m)*g/(M*l),0.]])
    B=np.array([[0],[1/M],[0],[-1/(M*l)]])
    return A,B

def controller(p=P,poles=POLES):
    """Ackermann pole placement, u = -K (state - desired_state)."""
    A,B=linear_model(p)
    controllability=np.column_stack([np.linalg.matrix_power(A,i)@B for i in range(4)])
    if np.linalg.matrix_rank(controllability)!=4:raise ValueError('System is not controllable')
    coefficients=np.poly(poles)
    polynomial=sum(coefficients[i]*np.linalg.matrix_power(A,4-i) for i in range(5))
    K=np.linalg.solve(controllability.T,np.array([0.,0,0,1]))@polynomial
    return K

# State weights correspond to [position, velocity, angle, angular velocity]
# in the SI units documented in README. The larger R penalises actuator effort.
LQR_WEIGHTS = {
    'gentle': ([10., 1., 100., 1.], 4.),
    'responsive': ([10., 1., 100., 1.], .1),
}

def lqr_controller(name='gentle', p=P):
    """Continuous-time LQR using the stable Hamiltonian invariant subspace.

    Solve A.T S + S A - S B R^-1 B.T S + Q = 0, then K = R^-1 B.T S.
    This small dense solver is for the documented four-state educational model.
    """
    weights, R = LQR_WEIGHTS[name]
    Q = np.diag(weights)
    A, B = linear_model(p)
    H = np.block([[A, -B @ B.T / R], [-Q, -A.T]])
    values, vectors = np.linalg.eig(H)
    stable = vectors[:, values.real < -1e-9]
    if stable.shape[1] != 4:
        raise ValueError('No separated four-dimensional stable subspace')
    S = np.linalg.solve(stable[:4].T, stable[4:].T).T
    if np.max(abs(S.imag)) > 1e-7:
        raise ValueError('Riccati solution is not real')
    S = (S.real + S.real.T) / 2
    K = (B.T @ S / R)[0]
    residual = A.T @ S + S @ A - S @ B @ B.T @ S / R + Q
    if np.linalg.norm(residual) > 1e-7 * max(1., np.linalg.norm(Q)):
        raise ValueError('Riccati residual is too large')
    if np.linalg.eigvalsh(S).min() <= 0 or np.linalg.eigvals(A-B@K[None,:]).real.max() >= 0:
        raise ValueError('LQR solution is not stabilising')
    return K, S

def energy(state,p=P):
    _,v,theta,omega=state
    return .5*(p.cart_mass+p.bob_mass)*v*v+p.bob_mass*p.length*v*omega*np.cos(theta)+.5*p.bob_mass*p.length**2*omega**2+p.bob_mass*p.gravity*p.length*np.cos(theta)

def rk4(state,t,dt,rhs):
    a=rhs(t,state);b=rhs(t+dt/2,state+dt*a/2);c=rhs(t+dt/2,state+dt*b/2);d=rhs(t+dt,state+dt*c)
    return state+dt*(a+2*b+2*c+d)/6

def simulate(initial_degrees=5.,task='balance',controlled=True,dt=.005,duration=12.,p=P,method="feedback"):
    if task not in ('balance','position','push'):raise ValueError('Unknown task')
    target=.5 if task=='position' else 0.
    desired=np.array([target,0.,0.,0.]);K=controller(p) if method=="feedback" else lqr_controller(method,p)[0]
    state=np.array([0.,0.,np.deg2rad(initial_degrees),0.])
    def inputs(t,s):
        command=float(np.clip(-K@(s-desired),-p.force_limit,p.force_limit)) if controlled else 0.
        disturbance=3. if task=='push' and 4.<=t<4.2 else 0.
        return command,disturbance
    def rhs(t,s):return dynamics(s,sum(inputs(t,s)),p)
    rows=[];reason='completed'
    for i in range(round(duration/dt)+1):
        t=i*dt;u,d=inputs(t,state)
        rows.append([t,*state,u,d])
        if abs(state[2])>np.deg2rad(60):reason='tilt_limit';break
        if abs(state[0])>2.:reason='track_limit';break
        if i<round(duration/dt):state=rk4(state,t,dt,rhs)
    data=np.asarray(rows)
    within=(abs(data[:,1]-target)<=.02)&(abs(data[:,3])<=np.deg2rad(1))&(abs(data[:,2])<=.03)&(abs(data[:,4])<=.05)
    after=4.2 if task=='push' else 0.
    bad=np.flatnonzero(~within | (data[:,0]<after))
    first=int(bad[-1]+1) if len(bad) else 0
    settling=float(data[first,0]) if reason=='completed' and first<len(data)-1 and data[-1,0]-data[first,0]>=1 else None
    metrics=dict(status=reason,settling_time_s=settling,peak_angle_deg=float(np.max(abs(np.rad2deg(data[:,3])))),
        peak_force_N=float(np.max(abs(data[:,5]))),final_position_error_m=float(data[-1,1]-target),
        final_angle_deg=float(np.rad2deg(data[-1,3])),end_time_s=float(data[-1,0]),
        force_squared_integral_N2s=float(np.sum(np.diff(data[:,0])*(data[1:,5]**2+data[:-1,5]**2)/2)))
    return data,metrics
