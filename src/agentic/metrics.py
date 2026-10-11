"""Metrics use physical units and rank failures before performance cost."""
import numpy as np


def evaluate(result, *, after=0.):
    t, s, u = result.time, result.states, result.control_force
    within = ((abs(s[:,0]) <= .02) & (abs(s[:,1]) <= .03)
              & (np.max(abs(s[:,2::2]), axis=1) <= np.deg2rad(1))
              & (np.max(abs(s[:,3::2]), axis=1) <= .05))
    bad = np.flatnonzero(~within | (t < after - 1e-10))
    first = int(bad[-1]+1) if len(bad) else 0
    absolute = (float(t[first]) if result.status == 'completed' and first < len(t)
                and t[-1]-t[first] >= 1-1e-10 else None)
    intervals = np.diff(t)
    effort = float(np.sum(intervals * (u[:-1]**2+u[1:]**2)/2))
    peak = float(np.max(abs(s[:,0])))
    return dict(status=result.status, end_s=float(t[-1]),
                settling_s=None if absolute is None else max(0., absolute-after),
                settling_absolute_s=absolute, peak_angle_deg=float(np.rad2deg(abs(s[:,2::2]).max())),
                peak_cart_m=peak, peak_force_N=float(abs(u).max()), effort_N2s=effort,
                saturation_fraction=float(np.sum(intervals*(abs(u[:-1]) >= 8-1e-9))/t[-1]) if t[-1] else 0.,
                constraint_satisfied=result.status == 'completed' and absolute is not None and peak <= .5,
                error=result.error)


def rank(metrics_list):
    if not metrics_list:
        raise ValueError('Cannot rank an empty experiment')
    failures = sum(m['status'] != 'completed' or m['settling_s'] is None for m in metrics_list)
    constraints = sum(m['peak_cart_m'] > .5 for m in metrics_list)
    costs = [(m['settling_s']/12 if m['settling_s'] is not None else 1.)
             + m['peak_cart_m']/.5 + m['effort_N2s']/(64*12) for m in metrics_list]
    return int(failures), int(constraints), float(np.mean(costs))
