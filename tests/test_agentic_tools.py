import sys, unittest, tempfile, json
from pathlib import Path
from unittest.mock import patch
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from agentic.store import ExperimentStore
from agentic.tools import ExperimentTools
from agentic.simulation import SimulationResult

# Fast simulator for orchestration tests: physics is exercised in numerical tests.
def simple_simulator(scenario, parameters, *, duration, dt):
    t=np.array([0., duration]); s=np.zeros((2,8))
    return SimulationResult(t,s,np.zeros(2),np.zeros(2),'completed')

class ToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.store=ExperimentStore(self.temp.name,metadata={'policy':'test'})
        self.tools=ExperimentTools(self.store,candidate_budget=2,tool_budget=10,
                                   simulator=simple_simulator)
    def test_full_suite_logs_provenance_and_winner(self):
        a=self.tools.dispatch('run_experiment',{})
        self.assertEqual(len(a['scenarios']),4)
        self.tools.dispatch('set_controller_parameters',{'changes':{'cart':2}})
        b=self.tools.dispatch('run_experiment',{})
        self.assertEqual(self.tools.best()['id'],a['id'])
        self.assertIn('error',self.tools.dispatch('run_experiment',{}))
        self.assertEqual(self.tools.remaining_candidates,0)
        comparison=self.tools.dispatch('compare_experiments',{'experiment_ids':[b['id'],a['id']]})
        self.assertEqual(comparison['winner'],a['id'])
        rows=[json.loads(s) for s in (self.store.run_dir/'events.jsonl').read_text().splitlines()]
        self.assertIn('git_revision',rows[0]['payload'])
        self.assertIn('versions',rows[0]['payload'])
        for path in a['trajectories'].values(): self.assertTrue((self.store.run_dir/path).exists())
        other=ExperimentStore(self.temp.name,metadata={})
        self.assertNotEqual(self.store.run_dir,other.run_dir)
    def test_rejections_are_atomic_and_consume_calls(self):
        before=self.tools.remaining_calls
        for name,args in [('get_experiment',{'experiment_id':'../outside'}),
                          ('run_experiment',{'path':'bad'}), ('unknown',{}),
                          ('set_controller_parameters',{'changes':{'cart':2,'effort':0}}),
                          ('run_experiment',{'rationale':'x'*2001}),
                          ('run_experiment',{'rationale':float('nan')}),
                          ('run_experiment',[]), ('set_controller_parameters',{'changes':{'__class__':1}})]:
            self.assertIn('error',self.tools.dispatch(name,args))
        self.assertEqual(self.tools.remaining_calls,before-8)
        a=self.tools.dispatch('run_experiment',{})
        self.assertEqual(a['parameters']['cart'],1)
    def test_failure_persisted_and_write_errors_propagate(self):
        def fail(*a,**k): raise ArithmeticError('simulation broke')
        tools=ExperimentTools(self.store,simulator=fail)
        result=tools.dispatch('run_experiment',{})
        self.assertEqual(result['rank'][0],4)
        self.assertEqual(len(result['scenarios']),4)
        self.assertIsNone(next(iter(result['scenarios'].values()))['settling_s'])
        json.dumps(result,allow_nan=False)
        with patch.object(self.store,'event',side_effect=OSError('disk full')):
            with self.assertRaises(OSError): tools.dispatch('run_experiment',{})
    def test_budget_validation_and_exhaustion(self):
        for value in [0,-1,True,1.2]:
            with self.assertRaises(ValueError): ExperimentTools(self.store,candidate_budget=value)
        tools=ExperimentTools(self.store,tool_budget=1,simulator=simple_simulator)
        tools.dispatch('unknown',{})
        self.assertIn('error',tools.dispatch('run_experiment',{}))
        self.assertIsNone(tools.best())
    def test_store_rejects_nonfinite_event(self):
        with self.assertRaises(ValueError): self.store.event('bad',{'x':float('nan')})
