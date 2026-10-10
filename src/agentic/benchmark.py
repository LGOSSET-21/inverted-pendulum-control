"""Offline, held-out comparison with equal tuning budgets and refinement."""
from dataclasses import asdict
import json
from pathlib import Path
from time import perf_counter
import numpy as np
from .agent import run_offline
from .simulation import ControllerParameters, run_simulation
from .metrics import evaluate, rank
from .scenarios import tuning_scenarios, validation_scenarios
from .store import ExperimentStore, provenance, write_json
from .tools import ExperimentTools, positive_int


def load_llm_summary(path):
    """Only import a completed, clean, same-revision run on this exact suite."""
    try:
        summary=json.loads(Path(path).read_text())
        best=summary['best']
        if (summary['policy'] != 'llm' or not summary['model']
            or summary['status'] not in ('model_stopped','budget_exhausted')
            or summary['provenance']['git_dirty'] is not False
            or summary['provenance']['git_revision'] != provenance()['git_revision']
            or best['settings'] != dict(duration=12.,dt=.0025,rod_mass=.01)
            or best['scenario_definitions'] != json.loads(json.dumps([asdict(s) for s in tuning_scenarios()]))):
            raise ValueError('Incompatible LLM run')
        ControllerParameters(**best['parameters'])
        positive_int(summary['candidates'],'candidate count')
        return summary
    except (KeyError,TypeError,json.JSONDecodeError) as exc:
        raise ValueError('Incompatible LLM summary') from exc


def refinement_report(coarse, fine, *, after):
    overlap=coarse.time <= fine.time[-1]+1e-10
    interpolated=np.column_stack([np.interp(coarse.time[overlap],fine.time,fine.states[:,i]) for i in range(8)])
    difference=float(np.max(abs(coarse.states[overlap]-interpolated)))
    a,b=evaluate(coarse,after=after),evaluate(fine,after=after)
    settling=(None if a['settling_s'] is None or b['settling_s'] is None
              else float(abs(a['settling_s']-b['settling_s'])))
    disagreement=coarse.status != fine.status
    return dict(max_state_difference=difference,settling_difference_s=settling,
                settling_disagreement=(a['settling_s'] is None) != (b['settling_s'] is None),
                status_disagreement=disagreement,coarse_status=coarse.status,fine_status=fine.status,
                warning=disagreement or difference>.01 or (a['settling_s'] is None)!=(b['settling_s'] is None))


def render_markdown(report):
    lines=['# Agent V1 — held-out benchmark','',
           'One deterministic run and one random-search seed; no statistical superiority claim.',
           'Offline means adaptive coordinate search, not an LLM. Failures remain in the table.',
           '',f"Source revision: `{report['provenance']['git_revision']}`; dirty: {report['provenance']['git_dirty']}.",
           f"Random seed: {report['seed']}. Baseline has no search; candidate counts include the original controller.",
           '', '| Method | Candidates | Tuning failed/unsettled | Validation failed/unsettled | Validation travel violations | Validation cost |',
           '|---|---:|---:|---:|---:|---:|']
    for name,method in report['methods'].items():
        failures=method.get('tuning_rank',[None])[0]
        lines.append(f"| {name} | {method['candidates']} | {failures if failures is not None else '—'} | {method['validation_rank'][0]} | {method['validation_rank'][1]} | {method['validation_rank'][2]:.4f} |")
    lines += ['', '| Method | Scenario | Status | Settling after disturbance (s) | Peak cart (m) | Effort (N²s) |',
              '|---|---|---|---:|---:|---:|']
    for name,method in report['methods'].items():
        for scenario,m in method['validation'].items():
            settling='—' if m['settling_s'] is None else f"{m['settling_s']:.4f}"
            lines.append(f"| {name} | {scenario} | {m['status']} | {settling} | {m['peak_cart_m']:.4f} | {m['effort_N2s']:.4f} |")
    lines += ['', '## Numerical refinement', '',
              'Selected controllers are replayed at dt/2. State error is measured on the common time interval.',
              'Warning threshold: >0.01 in any SI state component, completion-status disagreement, or settling-presence disagreement.',
              '', '| Method | Scenario | Max state difference | Settling difference (s) | Warning |',
              '|---|---|---:|---:|---|']
    for name,method in report['methods'].items():
        for scenario,r in method.get('refinement',{}).items():
            lines.append(f"| {name} | {scenario} | {r['max_state_difference']:.6g} | {r['settling_difference_s']} | {r['warning']} |")
    lines += ['', '## Accounting', '', f"Simulation counts: `{json.dumps(report['counts'])}`.",
              'Runtime and chosen parameter factors are in benchmark.json. Full events and trajectories are in the generated run directory.',
              'Peak angle/force, saturation, constraints, and failure details are retained in JSON.',
              'This is local simulated recovery; it is not a swing-up or hardware result.', '']
    return '\n'.join(lines)


def _run_benchmark(root, *, budget=12, seed=21, simulator=run_simulation, llm_summary=None):
    positive_int(budget,'budget')
    if isinstance(seed,bool) or not isinstance(seed,int) or seed < 0:
        raise ValueError('seed must be a nonnegative integer')
    imported=load_llm_summary(llm_summary) if llm_summary else None
    # Match actual LLM candidate count when comparing an imported run.
    if imported:
        budget=imported['candidates']
    start=perf_counter()
    methods={'baseline':dict(parameters=asdict(ControllerParameters()),candidates=0,tuning_runtime_s=0.)}
    for policy in ('offline','random'):
        store=ExperimentStore(root.run_dir,metadata=dict(policy=policy,seed=seed if policy=='random' else None))
        tools=ExperimentTools(store,candidate_budget=budget,tool_budget=max(60,2*budget),simulator=simulator)
        tick=perf_counter()
        if policy=='offline':
            selected=run_offline(tools)
            if selected['status'] == 'interrupted':
                raise KeyboardInterrupt()
        else:
            try:
                tools.dispatch('run_experiment',{'rationale':'Original controller baseline'})
                rng=np.random.default_rng(seed)
                while tools.remaining_candidates:
                    params=dict(zip(asdict(ControllerParameters()),np.exp(rng.uniform(np.log(.1),np.log(10),4)).tolist()))
                    tools.dispatch('set_controller_parameters',{'changes':params})
                    tools.dispatch('run_experiment',{'rationale':'Seeded log-uniform random search'})
                selected=dict(best=tools.best(),candidates=len(store.records()))
                store.event('session_end',selected)
                write_json(store.run_dir/'summary.json',selected)
            except KeyboardInterrupt:
                partial=dict(status='interrupted',best=tools.best(),candidates=len(store.records()))
                store.event('session_end',partial)
                write_json(store.run_dir/'summary.json',partial)
                raise
        methods[policy]=dict(parameters=selected['best']['parameters'],candidates=selected['candidates'],
            tuning_rank=selected['best']['rank'],tuning_runtime_s=perf_counter()-tick,
            tuning_log=str(store.run_dir.relative_to(root.run_dir)))
    if imported:
        methods['llm']=dict(parameters=imported['best']['parameters'],candidates=imported['candidates'],
            tuning_rank=imported['best']['rank'],model=imported['model'],tuning_runtime_s=None,
            source_provenance=imported['provenance'])
    # Selection is now frozen; only this stage can see validation observations.
    root.event('selection_frozen',methods)
    counts=dict(tuning_simulations=sum(m['candidates']*4 for name,m in methods.items() if name!='llm'),
                imported_tuning_simulations=imported['candidates']*4 if imported else 0,
                validation_simulations=0,refinement_simulations=0)
    for name,method in methods.items():
        tick=perf_counter(); metrics={}; trajectories={}; refinement={}
        params=ControllerParameters(**method['parameters'])
        for scenario in validation_scenarios():
            try:
                after=scenario.pulse.end_s if scenario.pulse else 0.
                result=simulator(scenario,params,duration=12.,dt=.0025)
                counts['validation_simulations']+=1
                trajectories[scenario.name]=result
                metrics[scenario.name]=evaluate(result,after=after)
                if name!='baseline':
                    fine=simulator(scenario,params,duration=12.,dt=.00125)
                    counts['refinement_simulations']+=1
                    refinement[scenario.name]=refinement_report(result,fine,after=after)
                    trajectories[scenario.name+'_refined']=fine
            except KeyboardInterrupt:
                root.save_experiment(dict(id='validation-'+name,status='interrupted',eligible=False,
                    validation=metrics),trajectories)
                raise
        method.update(validation=metrics,validation_rank=list(rank(list(metrics.values()))),
                      refinement=refinement,evaluation_runtime_s=perf_counter()-tick)
        root.save_experiment(dict(id='validation-'+name,**method),trajectories)
    report=dict(provenance=root.metadata,seed=seed,candidate_budget=budget,methods=methods,counts=counts,
                settings=dict(duration=12.,dt=.0025,refinement_dt=.00125),runtime_s=perf_counter()-start)
    write_json(root.run_dir/'benchmark.json',report)
    with (root.run_dir/'benchmark.md').open('x') as stream:
        stream.write(render_markdown(report))
    root.event('benchmark_complete',dict(counts=counts,runtime_s=report['runtime_s']))
    return dict(run_dir=str(root.run_dir),counts=counts,
                validation_ranks={name:m['validation_rank'] for name,m in methods.items()})


def run_benchmark(output_root, *, budget=12, seed=21, simulator=run_simulation, llm_summary=None):
    positive_int(budget, 'budget')
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError('seed must be a nonnegative integer')
    if llm_summary:
        load_llm_summary(llm_summary)
    root = ExperimentStore(output_root, metadata=dict(policy='benchmark', seed=seed))
    try:
        return _run_benchmark(root, budget=budget, seed=seed, simulator=simulator, llm_summary=llm_summary)
    except KeyboardInterrupt:
        result = dict(status='interrupted', run_dir=str(root.run_dir),
                      saved_evaluations=[r['id'] for r in root.records()])
        root.event('benchmark_interrupted', result)
        write_json(root.run_dir / 'interrupted.json', result)
        return result
