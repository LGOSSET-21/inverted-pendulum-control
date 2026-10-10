"""Parameterized upright experiments using the original massive-rod equations."""
from dataclasses import dataclass, asdict
from numbers import Real
from typing import Optional
import numpy as np
from scipy.linalg import solve_continuous_are
from massive_rods import Model
from pendulum import rk4
from triple_pendulum import Q, R


def finite_number(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real) or not np.isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    return float(value)


@dataclass(frozen=True)
class ControllerParameters:
    cart: float = 1.
    angles: float = 1.
    velocities: float = 1.
    effort: float = 1.

    def __post_init__(self):
        for key, value in asdict(self).items():
            value = finite_number(value, key)
            if not .1 <= value <= 10:
                raise ValueError(f'{key} must be in [0.1, 10]')
            object.__setattr__(self, key, value)


@dataclass(frozen=True)
class Pulse:
    force_N: float
    start_s: float
    end_s: float

    def __post_init__(self):
        for key, value in asdict(self).items():
            object.__setattr__(self, key, finite_number(value, key))
        if not 0 <= self.start_s < self.end_s:
            raise ValueError('Pulse requires 0 <= start < end')


@dataclass(frozen=True)
class Scenario:
    name: str
    initial_state: tuple
    pulse: Optional[Pulse] = None

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name or len(self.name) > 100:
            raise ValueError('Scenario requires a short name')
        if len(self.initial_state) != 8:
            raise ValueError('State must have eight SI components')
        object.__setattr__(self, 'initial_state', tuple(finite_number(v, 'state') for v in self.initial_state))
        if self.pulse is not None and not isinstance(self.pulse, Pulse):
            raise ValueError('pulse must be a Pulse')


@dataclass
class SimulationResult:
    time: np.ndarray
    states: np.ndarray
    control_force: np.ndarray
    disturbance: np.ndarray
    status: str
    error: Optional[str] = None


def validate_grid(scenario, duration, dt):
    duration, dt = finite_number(duration, 'duration'), finite_number(dt, 'dt')
    if duration <= 0 or dt <= 0 or dt > duration:
        raise ValueError('Require 0 < dt <= duration')
    times = [duration]
    if scenario.pulse:
        if scenario.pulse.end_s > duration:
            raise ValueError('Pulse ends beyond simulation horizon')
        times += [scenario.pulse.start_s, scenario.pulse.end_s]
    if any(not np.isclose(t / dt, round(t / dt), rtol=0, atol=1e-8) for t in times):
        raise ValueError('Duration and pulse boundaries must lie on the integration grid')
    if duration / dt > 1_000_000:
        raise ValueError('At most one million integration intervals')
    return duration, dt


def run_simulation(scenario, parameters=ControllerParameters(), *, duration=12., dt=.0025):
    duration, dt = validate_grid(scenario, duration, dt)
    if not isinstance(parameters, ControllerParameters):
        raise ValueError('parameters must be ControllerParameters')
    model = Model(rod_mass=.01)
    state = np.array(scenario.initial_state)
    rows, status, error = [], 'completed', None
    try:
        weights = Q.copy()
        weights[0] *= parameters.cart
        weights[2::2] *= parameters.angles
        weights[1::2] *= parameters.velocities
        effort = R * parameters.effort
        A, B = model.linear_model()
        P = solve_continuous_are(A, B, np.diag(weights), [[effort]])
        gain = (B.T @ P / effort)[0]
        if not np.isfinite(gain).all() or np.linalg.eigvals(A-B@gain[None,:]).real.max() >= 0:
            raise ArithmeticError('Unstable or nonfinite linear controller')
        for i in range(round(duration / dt)+1):
            t = round(i * dt, 12)
            force = float(np.clip(-gain @ state, -8, 8))
            pulse = scenario.pulse
            push = pulse.force_N if pulse and pulse.start_s <= t < pulse.end_s else 0.
            rows.append([t, *state, force, push])
            if np.max(np.abs(state[2::2])) > np.deg2rad(60):
                status = 'tilt_limit'; break
            if abs(state[0]) > 2:
                status = 'track_limit'; break
            if i < round(duration / dt):
                with np.errstate(over='raise', invalid='raise', divide='raise'):
                    state = rk4(state, t, dt, lambda tt, ss: model.dynamics(ss, float(np.clip(-gain@ss, -8, 8))+push))
                if not np.isfinite(state).all():
                    raise ArithmeticError('Nonfinite integration state')
    except (ArithmeticError, ValueError, np.linalg.LinAlgError) as exc:
        status, error = 'numerical_failure', type(exc).__name__
    if not rows:
        rows = [[0., *scenario.initial_state, 0., 0.]]
    data = np.asarray(rows)
    return SimulationResult(data[:,0], data[:,1:9], data[:,9], data[:,10], status, error)
