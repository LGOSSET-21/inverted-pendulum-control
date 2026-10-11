"""Regenerate figures from archived validation traces (numpy, matplotlib)."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
COLORS = ['#64748b', '#087e8b']
LABELS = ['Original controller', 'Codex-selected parameters']
plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
records = [json.loads((ROOT / ('validation-' + n) / 'experiment.json').read_text())
           for n in ['baseline', 'codex_demo']]
fig, axes = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
for record, color, label in zip(records, COLORS, LABELS):
    trace = np.load(ROOT / record['trajectories']['validation_push'])
    t = trace['time'] - 5.2
    axes[0].plot(t, np.rad2deg(np.abs(trace['states'][:, [2, 4, 6]])).max(axis=1), color=color, label=label)
    axes[1].plot(t, trace['states'][:, 0] * 100, color=color)
    axes[2].plot(t, trace['control_force'], color=color)
for ax in axes:
    ax.axvspan(-.2, 0, color='#fbbf24', alpha=.25)
    ax.grid(alpha=.2)
    ax.set_xlim(-.4, 3)
axes[0].set_ylabel('Max absolute angle (deg)')
axes[1].set_ylabel('Cart position (cm)')
axes[2].set_ylabel('Control force (N)')
axes[2].set_xlabel('Time after disturbance ends (s)')
axes[0].legend(loc='upper right')
fig.suptitle('Validation push: faster recovery with the selected parameters\nShaded interval: external force of -2 N', fontsize=13)
fig.tight_layout(rect=(0, 0, 1, .94))
fig.savefig(ROOT / 'push-recovery.png', dpi=160)
plt.close(fig)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
scenarios = ['validation_aligned', 'validation_push', 'validation_offset']
x = np.arange(3)
for i, (record, color, label) in enumerate(zip(records, COLORS, LABELS)):
    values = [record['metrics'][s]['settling_s'] for s in scenarios]
    bars = axes[0].bar(x + (i-.5)*.35, values, .35, color=color, label=label)
    axes[0].bar_label(bars, fmt='%.3f', padding=3, fontsize=9)
    trace = np.load(ROOT / record['trajectories']['validation_opposed'])
    axes[1].plot(trace['time'], np.rad2deg(np.abs(trace['states'][:, [2,4,6]])).max(axis=1), color=color, label=label)
axes[0].set_xticks(x, ['Aligned tilt', 'Push', 'Cart offset'])
axes[0].set_ylim(0, 3)
axes[0].set_ylabel('Settling time (s)')
axes[0].set_title('Three successful validation scenarios')
axes[1].axhline(60, color='#b91c1c', linestyle='--', label='60-degree stop threshold')
axes[1].set_xlabel('Time (s)')
axes[1].set_ylabel('Max absolute angle (deg)')
axes[1].set_title('Opposing tilts: both controllers fail')
for ax in axes:
    ax.grid(axis='y', alpha=.2)
axes[1].legend(fontsize=8)
fig.tight_layout()
fig.savefig(ROOT / 'validation-overview.png', dpi=160)
plt.close(fig)
print('Generated two figures from archived traces.')
