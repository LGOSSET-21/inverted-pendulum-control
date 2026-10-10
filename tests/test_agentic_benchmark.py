import sys, unittest, tempfile, json
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from agentic.benchmark import run_benchmark, refinement_report, load_llm_summary
from agentic.scenarios import tuning_scenarios, validation_scenarios
from agentic.simulation import SimulationResult
from test_agentic_tools import simple_simulator

class BenchmarkTests(unittest.TestCase):
    def test_separation_budgets_reports_and_baseline(self):
        calls=[]
        def simulator(scenario,params,**kwargs):
            calls.append((scenario.name,params,kwargs['dt']))
            return simple_simulator(scenario,params,**kwargs)
        with tempfile.TemporaryDirectory() as directory:
            result=run_benchmark(directory,budget=3,seed=21,simulator=simulator)
            report=json.loads((Path(result['run_dir'])/'benchmark.json').read_text())
            self.assertEqual(report['methods']['offline']['candidates'],3)
            self.assertEqual(report['methods']['random']['candidates'],3)
            self.assertEqual(report['methods']['baseline']['parameters']['cart'],1)
            self.assertEqual(report['counts']['tuning_simulations'],24)
            self.assertEqual(report['counts']['validation_simulations'],12)
            self.assertEqual(report['counts']['refinement_simulations'],8)
            self.assertTrue(all(name.startswith('train_') for name,_,_ in calls[:24]))
            self.assertTrue(all(name.startswith('validation_') for name,_,_ in calls[24:]))
            self.assertEqual(len(report['methods']['offline']['validation']),4)
            self.assertTrue((Path(result['run_dir'])/'benchmark.md').exists())
            self.assertFalse(set(s.name for s in tuning_scenarios()) & set(s.name for s in validation_scenarios()))
    def test_refinement_flags_disagreement(self):
        t=np.array([0.,1.,2.]); zeros=np.zeros((3,8))
        a=SimulationResult(t,zeros,np.zeros(3),np.zeros(3),'completed')
        b=SimulationResult(t,zeros+.02,np.zeros(3),np.zeros(3),'tilt_limit')
        report=refinement_report(a,b,after=0)
        self.assertTrue(report['warning'])
        self.assertTrue(report['status_disagreement'])
        self.assertAlmostEqual(report['max_state_difference'],.02)
    def test_reports_retain_failures(self):
        def failed(scenario,params,**kwargs):
            r=simple_simulator(scenario,params,**kwargs); r.status='tilt_limit'; return r
        with tempfile.TemporaryDirectory() as directory:
            result=run_benchmark(directory,budget=1,simulator=failed)
            report=json.loads((Path(result['run_dir'])/'benchmark.json').read_text())
            for method in report['methods'].values():
                self.assertEqual(method['validation_rank'][0],4)
                self.assertIsNone(next(iter(method['validation'].values()))['settling_s'])
    def test_incompatible_llm_summary_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'summary.json'
            path.write_text(json.dumps({'policy':'offline'}))
            with self.assertRaises(ValueError): load_llm_summary(path)

    def test_imported_short_run_matches_budget(self):
        from unittest.mock import patch
        from dataclasses import asdict
        from agentic.store import provenance
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'summary.json'
            imported=dict(policy='llm',model='test-model',status='model_stopped',candidates=1,
                provenance={'git_dirty':False,'git_revision':provenance()['git_revision']},
                best=dict(parameters=dict(cart=1.,angles=1.,velocities=1.,effort=1.),rank=[0,0,0.],
                          settings=dict(duration=12.,dt=.0025,rod_mass=.01),
                          scenario_definitions=[asdict(s) for s in tuning_scenarios()]))
            path.write_text(json.dumps(imported))
            result=run_benchmark(directory,budget=12,llm_summary=path,simulator=simple_simulator)
            report=json.loads((Path(result['run_dir'])/'benchmark.json').read_text())
            self.assertEqual(report['candidate_budget'],1)
            self.assertEqual(report['methods']['random']['candidates'],1)
            self.assertEqual(report['methods']['offline']['candidates'],1)
