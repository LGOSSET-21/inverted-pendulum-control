import sys, unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from agentic.simulation import ControllerParameters, Pulse, Scenario, SimulationResult, run_simulation
from agentic.metrics import evaluate, rank
from agentic.scenarios import tuning_scenarios
from massive_rods import Model

class SimulationTests(unittest.TestCase):
    def test_default_matches_original(self):
        actual = run_simulation(tuning_scenarios()[0])
        expected, metrics = Model().simulate()
        np.testing.assert_allclose(actual.states, expected[:, 1:9], atol=1e-10)
        self.assertEqual(evaluate(actual)['settling_s'], metrics['settling_s'])

    def test_equilibrium(self):
        result = run_simulation(Scenario('zero', (0.,)*8), duration=1)
        self.assertEqual(evaluate(result)['settling_s'], 0)
        self.assertEqual(evaluate(result)['effort_N2s'], 0)

    def test_post_pulse_settling_and_hold(self):
        t = np.arange(0, 4.01, .1)
        s = np.zeros((len(t), 8)); s[20:26, 0] = .03
        result = SimulationResult(t, s, np.zeros(len(t)), np.zeros(len(t)), 'completed')
        m = evaluate(result, after=2.2)
        self.assertAlmostEqual(m['settling_s'], .4)
        self.assertAlmostEqual(m['settling_absolute_s'], 2.6)
        self.assertIsNone(evaluate(result, after=3.5)['settling_s'])
        result.status = 'tilt_limit'
        self.assertIsNone(evaluate(result)['settling_s'])

    def test_validation(self):
        for value in [float('nan'), float('inf'), True, 0, 11, '1']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                ControllerParameters(cart=value)
        with self.assertRaises(TypeError): ControllerParameters(other=1)
        for state in [(0,)*7, (float('nan'),)*8, (True,)*8]:
            with self.assertRaises(ValueError): Scenario('bad', state)
        for kwargs in [dict(dt=0), dict(dt=True), dict(duration=.001),
                       dict(duration=float('inf'))]:
            with self.assertRaises(ValueError): run_simulation(Scenario('z',(0,)*8), **kwargs)
        for pulse in [Pulse(1, .001, .2), Pulse(1, .1, 2)]:
            with self.assertRaises(ValueError): run_simulation(Scenario('z',(0,)*8,pulse),duration=1)

    def test_limits_and_solver_failure(self):
        for state, status in [((3,0,0,0,0,0,0,0),'track_limit'),
                              ((0,0,2,0,0,0,0,0),'tilt_limit')]:
            r=run_simulation(Scenario('limit',state),duration=1)
            self.assertEqual(r.status,status)
            self.assertIsNone(evaluate(r)['settling_s'])
        with patch('agentic.simulation.rk4', side_effect=ArithmeticError('fail')):
            r=run_simulation(Scenario('z',(0,)*8),duration=1)
        self.assertEqual(r.status,'numerical_failure')
        with patch('agentic.simulation.rk4', return_value=np.full(8,np.nan)):
            r=run_simulation(Scenario('z',(0,)*8),duration=1)
        self.assertEqual(r.status,'numerical_failure')
        self.assertTrue(np.isfinite(r.states).all())

    def test_rank_prefers_success(self):
        r=run_simulation(Scenario('zero',(0,)*8),duration=1)
        good=evaluate(r); bad=dict(good,status='tilt_limit',settling_s=None)
        expensive=dict(good,effort_N2s=1000,peak_cart_m=.6)
        self.assertLess(rank([expensive]),rank([bad]))

    def test_calculated_pulse_boundaries_match_literal(self):
        a=run_simulation(Scenario('a',(0.,)*8,Pulse(1,.1+.2,.4)),duration=1,dt=.1)
        b=run_simulation(Scenario('b',(0.,)*8,Pulse(1,.3,.4)),duration=1,dt=.1)
        np.testing.assert_array_equal(a.disturbance,b.disturbance)
        np.testing.assert_allclose(a.states,b.states)

    def test_extreme_states_rejected_before_numerics(self):
        for state in [(0,0,1e308,0,0,0,0,0),(1e308,)*8]:
            with self.assertRaises(ValueError): Scenario('extreme',state)
