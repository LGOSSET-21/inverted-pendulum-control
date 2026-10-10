"""Run from repo root: PYTHONPATH=src python -m agentic tune --policy offline."""
import argparse
import json
from pathlib import Path
from .agent import run_offline, run_llm
from .llm import OpenAITransport
from .store import ExperimentStore
from .tools import ExperimentTools, positive_int


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['tune','benchmark'])
    parser.add_argument('--policy',choices=['offline','llm'],default='offline')
    parser.add_argument('--model')
    parser.add_argument('--budget',type=int,default=12)
    parser.add_argument('--tool-budget',type=int,default=60)
    parser.add_argument('--seed',type=int,default=21)
    parser.add_argument('--output',type=Path,default=Path('runs'))
    args=parser.parse_args(argv)
    try:
        positive_int(args.budget,'budget'); positive_int(args.tool_budget,'tool budget')
        if args.command == 'benchmark':
            if args.policy != 'offline' or args.model:
                raise ValueError('Benchmark is offline; run tune --policy llm separately')
            from .benchmark import run_benchmark
            result=run_benchmark(args.output,budget=args.budget,seed=args.seed)
            print(json.dumps(result,indent=2,allow_nan=False)); return 0
        if args.policy == 'llm' and not args.model:
            raise ValueError('--model is required for LLM mode')
        transport=OpenAITransport() if args.policy == 'llm' else None
        store=ExperimentStore(args.output,metadata=dict(policy=args.policy,model=args.model,seed=None))
        tools=ExperimentTools(store,candidate_budget=args.budget,tool_budget=args.tool_budget)
        result=(run_llm(tools,transport,model=args.model) if transport else run_offline(tools))
        print(json.dumps(dict(run_dir=str(store.run_dir),**result),indent=2,allow_nan=False))
        return 1 if result['status'] in ('api_error','protocol_error') else 0
    except (ValueError,OSError) as exc:
        parser.exit(2,f'Error: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
