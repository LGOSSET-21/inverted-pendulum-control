"""Optional Responses API transport. No SDK import or network until constructed.

Protocol: https://developers.openai.com/api/docs/guides/function-calling
All output items are returned for in-memory continuation, including reasoning.
"""
import os


def _object(properties):
    return dict(type='object',properties=properties,required=list(properties),additionalProperties=False)


def tool_schemas():
    factors={name:dict(type='number',minimum=.1,maximum=10) for name in ('cart','angles','velocities','effort')}
    entries=[
        ('set_controller_parameters','Set all four LQR factors; use current values for unchanged factors.',
         {'changes':_object(factors)}),
        ('run_experiment','Evaluate current parameters on all fixed tuning scenarios.',
         {'rationale':dict(type='string',maxLength=2000)}),
        ('get_experiment','Read a recorded experiment from this session.',{'experiment_id':dict(type='string')}),
        ('compare_experiments','Rank recorded experiments; smaller rank is better.',
         {'experiment_ids':dict(type='array',items=dict(type='string'),minItems=1,maxItems=100)})]
    return [dict(type='function',name=name,description=description,strict=True,parameters=_object(properties))
            for name,description,properties in entries]


class OpenAITransport:
    def __init__(self, *, client=None):
        if client is None:
            if not os.environ.get('OPENAI_API_KEY'):
                raise ValueError('Set OPENAI_API_KEY to use the LLM policy; offline mode needs no key')
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise ValueError('Install requirements-agent.txt for LLM mode') from exc
            client = OpenAI(timeout=60., max_retries=1)
        self.client = client

    def respond(self, messages, schemas, model):
        response = self.client.responses.create(model=model,input=messages,tools=schemas,
            parallel_tool_calls=False,store=False,include=['reasoning.encrypted_content'],
            max_output_tokens=2000)
        if response.status != 'completed':
            raise RuntimeError('Model response did not complete')
        return [item.model_dump(mode='json',exclude_none=True) for item in response.output]
