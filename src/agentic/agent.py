"""One supervisor, with deterministic and LLM decision policies."""
from dataclasses import asdict
import json
from .simulation import ControllerParameters
from .llm import tool_schemas
from .store import write_json


def _baseline(tools):
    if tools.store.records() or tools.parameters != ControllerParameters():
        raise ValueError('Start an agent with fresh tools at baseline parameters')
    result = tools.dispatch('run_experiment', {'rationale':'Original controller baseline'})
    if 'error' in result:
        raise ValueError('Could not evaluate baseline')
    return result


def _finish(tools, policy, status, model=None):
    result = dict(policy=policy, model=model, status=status, best=tools.best(),
                  candidates=len(tools.store.records()),
                  simulations=4*len(tools.store.records()),
                  remaining_calls=tools.remaining_calls, provenance=tools.store.metadata)
    tools.store.event('session_end',result)
    write_json(tools.store.run_dir/'summary.json',result)
    return result


def run_offline(tools):
    _baseline(tools)
    axes = list(asdict(ControllerParameters()))
    cycle_start, step, index = tools.best()['rank'], 2., 0
    while tools.remaining_candidates and tools.remaining_calls >= 2:
        params = tools.best()['parameters'].copy()
        axis = axes[(index//2)%4]
        factor = step if index%2 == 0 else 1/step
        params[axis] = min(10.,max(.1,params[axis]*factor))
        tools.dispatch('set_controller_parameters',{'changes':params})
        result = tools.dispatch('run_experiment',{'rationale':f'Coordinate search: {axis} times {factor:g}'})
        if 'error' in result:
            break
        index += 1
        if index % 8 == 0:
            if tools.best()['rank'] >= cycle_start:
                step = step**.5
            cycle_start = tools.best()['rank']
    return _finish(tools,'offline','budget_exhausted')


INSTRUCTIONS = '''You supervise upright massive-rod controller experiments.
Change only the four bounded LQR factors. The original candidate has already been
measured. Minimize lexicographically: failed/unsettled scenarios, scenarios above
0.5 m cart travel, mean normalized time+travel+force-squared cost. A smaller tuple
is better. Inspect measured results, propose a factor change, run an experiment,
and use observations to decide the next change. Continue until the candidate or
tool budget is used; do not repeat a candidate unnecessarily. The program selects
the best tested candidate. Give only short experimental rationales in tool calls.
You cannot change scenarios, physical equations, force/track/tilt limits or metric
thresholds. No executable code, files, or external tools are available.'''


def run_llm(tools, transport, *, model):
    if not isinstance(model,str) or not model.strip():
        raise ValueError('An explicit model identifier is required')
    baseline = _baseline(tools)
    messages = [dict(role='developer',content=INSTRUCTIONS),
                dict(role='user',content=json.dumps(dict(baseline=baseline,
                    candidate_budget_remaining=tools.remaining_candidates,
                    tool_budget_remaining=tools.remaining_calls)))]
    status = 'budget_exhausted'
    while tools.remaining_candidates and tools.remaining_calls:
        try:
            output = transport.respond(messages,tool_schemas(),model)
        except Exception as exc:
            # Provider errors may contain headers or credentials: store the type only.
            tools.store.event('api_error',{'error_type':type(exc).__name__})
            status='api_error'; break
        if not isinstance(output,list) or any(not isinstance(item,dict) for item in output):
            tools.store.event('protocol_error',{'error':'Invalid model output'})
            status='protocol_error'; break
        calls = [item for item in output if item.get('type') == 'function_call']
        if not calls:
            status='model_stopped'; break
        # Preserve protocol items (including encrypted reasoning) only in memory.
        messages.extend(output)
        for call in calls:
            if not tools.remaining_calls or not tools.remaining_candidates:
                break
            try:
                arguments = json.loads(call.get('arguments',''),
                    parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))
            except (ValueError,TypeError):
                arguments = None
            result = tools.dispatch(call.get('name'),arguments)
            call_id = call.get('call_id')
            if not isinstance(call_id,str) or not call_id:
                status='protocol_error'; break
            messages.append(dict(type='function_call_output',call_id=call_id,
                output=json.dumps(dict(result=result,remaining_candidates=tools.remaining_candidates,
                                       remaining_calls=tools.remaining_calls),allow_nan=False)))
        if status == 'protocol_error':
            break
    return _finish(tools,'llm',status,model)
