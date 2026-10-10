"""Four validated tools; budgets and candidate selection live outside the LLM."""
from dataclasses import asdict
import json
from time import perf_counter
import numpy as np
from .simulation import ControllerParameters, SimulationResult, run_simulation, validate_grid
from .metrics import evaluate, rank
from .scenarios import tuning_scenarios


def positive_int(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f'{name} must be a positive integer')
    return value


class ExperimentTools:
    def __init__(self, store, *, candidate_budget=12, tool_budget=60, duration=12., dt=.0025,
                 simulator=run_simulation):
        self.remaining_candidates = positive_int(candidate_budget, 'candidate budget')
        self.remaining_calls = positive_int(tool_budget, 'tool budget')
        self.store, self.duration, self.dt = store, duration, dt
        self.simulator, self.parameters = simulator, ControllerParameters()
        self._scenarios = tuning_scenarios()
        for scenario in self._scenarios:
            validate_grid(scenario, duration, dt)
        self.store.event('configuration', dict(candidate_budget=candidate_budget, tool_budget=tool_budget,
            duration=duration, dt=dt, scenarios=[asdict(s) for s in self._scenarios], rod_mass=.01,
            force_limit_N=8, track_limit_m=2, tilt_limit_deg=60))

    def dispatch(self, name, arguments):
        if self.remaining_calls <= 0:
            return {'error': 'Tool budget exhausted'}
        self.remaining_calls -= 1
        # Reject before logging arbitrary payloads (including nonfinite JSON).
        try:
            if not isinstance(name, str) or not isinstance(arguments, dict):
                raise ValueError('Tool name must be text and arguments an object')
            serialized = json.dumps(arguments, allow_nan=False)
            if len(serialized) > 10000:
                raise ValueError('Tool arguments too large')
            allowed = {'set_controller_parameters': {'changes'}, 'run_experiment': {'rationale'},
                       'get_experiment': {'experiment_id'}, 'compare_experiments': {'experiment_ids'}}
            if name not in allowed or set(arguments) - allowed[name]:
                raise ValueError('Unknown tool or unexpected arguments')
            if name == 'run_experiment':
                rationale = arguments.get('rationale', '')
                if not isinstance(rationale, str) or len(rationale) > 2000:
                    raise ValueError('Rationale must be text of at most 2000 characters')
            self.store.event('tool_call', dict(name=name, arguments=arguments, remaining_calls=self.remaining_calls))
            result = getattr(self, '_' + name)(**arguments)
        except (ValueError, TypeError, KeyError) as exc:
            result = {'error': str(exc)[:300]}
        self.store.event('tool_result', dict(name=name if isinstance(name,str) else 'invalid', result=result))
        return result

    def _set_controller_parameters(self, changes):
        if not isinstance(changes, dict) or not changes or set(changes) - set(asdict(self.parameters)):
            raise ValueError('Provide known controller factors')
        updated = ControllerParameters(**{**asdict(self.parameters), **changes})
        self.parameters = updated
        return {'parameters': asdict(updated)}

    def _run_experiment(self, rationale=''):
        if self.remaining_candidates <= 0:
            raise ValueError('Candidate budget exhausted')
        self.remaining_candidates -= 1
        experiment_id = f'exp-{len(self.store.records())+1:04d}'
        record = dict(id=experiment_id, parameters=asdict(self.parameters), rationale=rationale,
                      settings=dict(duration=self.duration, dt=self.dt, rod_mass=.01),
                      scenario_definitions=[asdict(s) for s in self._scenarios])
        self.store.event('experiment_start', record)
        start, trajectories, metrics = perf_counter(), {}, {}
        for scenario in self._scenarios:
            try:
                result = self.simulator(scenario, self.parameters, duration=self.duration, dt=self.dt)
            except KeyboardInterrupt:
                record.update(status='interrupted', eligible=False, scenarios=metrics, rank=None,
                              simulation_attempts=len(metrics)+1,
                              runtime_s=perf_counter()-start)
                self.store.save_experiment(record, trajectories)
                raise
            except (ArithmeticError, ValueError, np.linalg.LinAlgError) as exc:
                result = SimulationResult(np.array([0.]),np.array([scenario.initial_state]),
                    np.zeros(1),np.zeros(1),'numerical_failure',type(exc).__name__)
            trajectories[scenario.name] = result
            metrics[scenario.name] = evaluate(result, after=scenario.pulse.end_s if scenario.pulse else 0.)
        record.update(scenarios=metrics, rank=list(rank(list(metrics.values()))), runtime_s=perf_counter()-start)
        return self.store.save_experiment(record, trajectories)

    def _get_experiment(self, experiment_id):
        return self.store.get(experiment_id)

    def _compare_experiments(self, experiment_ids):
        if not isinstance(experiment_ids, list) or not 1 <= len(experiment_ids) <= 100:
            raise ValueError('Provide 1–100 experiment IDs')
        records = [self.store.get(key) for key in experiment_ids]
        if any(not r.get('eligible', True) for r in records):
            raise ValueError('Cannot rank an interrupted experiment')
        ordered = sorted(records, key=lambda r: (r['rank'], r['id']))
        return dict(winner=ordered[0]['id'], ordered=[dict(id=r['id'],rank=r['rank']) for r in ordered])

    def best(self):
        records = [r for r in self.store.records() if r.get('eligible', True)]
        return min(records, key=lambda r: (r['rank'],r['id'])) if records else None
