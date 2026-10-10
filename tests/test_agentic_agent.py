import sys, unittest, tempfile, json
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from agentic.agent import run_offline, run_llm
from agentic.llm import OpenAITransport, tool_schemas
from agentic.store import ExperimentStore
from agentic.tools import ExperimentTools
from test_agentic_tools import simple_simulator

class ScriptedTransport:
    def __init__(self, outputs): self.outputs=iter(outputs); self.observations=[]
    def respond(self,messages,schemas,model):
        self.observations.append(json.loads(json.dumps(messages)))
        return next(self.outputs)

def call(name,args,identifier='call-1'):
    return dict(type='function_call',call_id=identifier,name=name,arguments=json.dumps(args))

class AgentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
    def tools(self,**kwargs):
        return ExperimentTools(ExperimentStore(self.temp.name,metadata={'policy':'test'}),
                               simulator=simple_simulator,**kwargs)
    def test_offline_reproducible_and_budget(self):
        a,b=self.tools(candidate_budget=4),self.tools(candidate_budget=4)
        for tools in (a,b):
            result=run_offline(tools)
            self.assertEqual(result['candidates'],4)
            self.assertEqual(result['best']['parameters']['cart'],1)
        self.assertEqual([r['parameters'] for r in a.store.records()],
                         [r['parameters'] for r in b.store.records()])
    def test_llm_observations_and_measured_winner(self):
        tools=self.tools(candidate_budget=2)
        transport=ScriptedTransport([[call('set_controller_parameters',{'changes':{'cart':2}})],
                                     [call('run_experiment',{'rationale':'try cart'},'call-2')]])
        result=run_llm(tools,transport,model='test')
        self.assertEqual(result['candidates'],2)
        self.assertEqual(result['best']['id'],'exp-0001')
        self.assertIn('exp-0001',json.dumps(transport.observations[0]))
        self.assertIn('function_call_output',json.dumps(transport.observations[1]))
    def test_invalid_json_calls_bounded_and_text_not_winner(self):
        tools=self.tools(candidate_budget=3,tool_budget=4)
        transport=ScriptedTransport([[
            dict(type='function_call',call_id='a',name='run_experiment',arguments='{'),
            call('run_experiment',[],'b'), call('unknown',{},'c'),
            call('run_experiment',{},'d')]])
        result=run_llm(tools,transport,model='test')
        self.assertEqual(result['candidates'],1)
        self.assertEqual(tools.remaining_calls,0)
        result=run_llm(self.tools(),ScriptedTransport([[dict(type='message',content=[])] ]),model='test')
        self.assertEqual(result['status'],'model_stopped')
        self.assertEqual(result['candidates'],1)
    def test_api_failure_is_explicit_no_secret_in_log(self):
        tools=self.tools()
        class Broken:
            def respond(self,*args): raise RuntimeError('sk-DO-NOT-LOG')
        result=run_llm(tools,Broken(),model='test')
        self.assertEqual(result['status'],'api_error')
        self.assertEqual(result['candidates'],1)
        self.assertNotIn('sk-DO-NOT-LOG',(tools.store.run_dir/'events.jsonl').read_text())
    def test_transport_preserves_protocol_items_and_limits(self):
        response=SimpleNamespace(status='completed',output=[SimpleNamespace(model_dump=lambda **kw: call('run_experiment',{}))])
        class Responses:
            def create(self,**kwargs): self.kwargs=kwargs; return response
        client=SimpleNamespace(responses=Responses())
        transport=OpenAITransport(client=client)
        output=transport.respond([{'role':'user','content':'test'}],tool_schemas(),'test')
        self.assertEqual(output[0]['call_id'],'call-1')
        self.assertFalse(client.responses.kwargs['parallel_tool_calls'])
        self.assertFalse(client.responses.kwargs['store'])
        self.assertLessEqual(client.responses.kwargs['max_output_tokens'],4000)
        for schema in tool_schemas():
            self.assertFalse(schema['parameters']['additionalProperties'])
    def test_missing_model_and_short_call_budget(self):
        with self.assertRaises(ValueError): run_llm(self.tools(),None,model='')
        result=run_offline(self.tools(candidate_budget=3,tool_budget=2))
        self.assertEqual(result['candidates'],1)
