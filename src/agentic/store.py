"""Append-only events and exclusively created experiment artifacts."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import uuid
import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[2]


def provenance():
    def git(*args):
        try:
            return subprocess.check_output(['git', *args], cwd=ROOT, stderr=subprocess.DEVNULL,
                                           text=True, timeout=5).strip()
        except (OSError, subprocess.SubprocessError):
            return None
    status = git('status', '--porcelain')
    return dict(git_revision=git('rev-parse', 'HEAD'), git_dirty=None if status is None else bool(status),
                versions=dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__))


def write_json(path, value):
    text = json.dumps(value, allow_nan=False, indent=2)
    with Path(path).open('x', encoding='utf-8') as stream:
        stream.write(text + '\n')


class ExperimentStore:
    def __init__(self, output_root, *, metadata):
        self.run_dir = Path(output_root) / ('run-' + uuid.uuid4().hex)
        self.run_dir.mkdir(parents=True, exist_ok=False)
        self._records = {}
        self.metadata = {**provenance(), **metadata}
        self.event('session_start', self.metadata)

    def event(self, kind, payload):
        row = dict(time_utc=datetime.now(timezone.utc).isoformat(), kind=kind, payload=payload)
        text = json.dumps(row, allow_nan=False)
        with (self.run_dir / 'events.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(text + '\n')
            stream.flush()

    def save_experiment(self, record, trajectories):
        record = copy.deepcopy(record)
        artifact_dir = self.run_dir / record['id']
        artifact_dir.mkdir(exist_ok=False)
        record['trajectories'] = {}
        for index, (name, result) in enumerate(trajectories.items()):
            path = artifact_dir / f'trajectory-{index}.npz'
            with path.open('xb') as stream:
                np.savez_compressed(stream, time=result.time, states=result.states,
                                    control_force=result.control_force, disturbance=result.disturbance)
            record['trajectories'][name] = str(path.relative_to(self.run_dir))
        write_json(artifact_dir / 'experiment.json', record)
        self.event('experiment_complete', record)
        self._records[record['id']] = record
        return copy.deepcopy(record)

    def get(self, experiment_id):
        if not isinstance(experiment_id, str) or experiment_id not in self._records:
            raise ValueError('Unknown experiment ID in this session')
        return copy.deepcopy(self._records[experiment_id])

    def records(self):
        return copy.deepcopy(list(self._records.values()))
