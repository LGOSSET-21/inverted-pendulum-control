"""Fixed tuning/held-out scenarios; neither suite is changed by the agent."""
import numpy as np
from .simulation import Scenario, Pulse


def _tilt(name, angles):
    s = np.zeros(8); s[2::2] = np.deg2rad(angles)
    return Scenario(name, tuple(s))


def tuning_scenarios():
    return (_tilt('train_aligned', [1,1,1]), _tilt('train_opposed', [1,-1,1]),
            Scenario('train_push', (0.,)*8, Pulse(3,4,4.2)),
            Scenario('train_offset', (.05,0,0,0,0,0,0,0)))


def validation_scenarios():
    return (_tilt('validation_aligned', [-1.5]*3), _tilt('validation_opposed', [-.75,.75,-.75]),
            Scenario('validation_push', (0.,)*8, Pulse(-2,5,5.2)),
            Scenario('validation_offset', (-.075,0,0,0,0,0,0,0)))
