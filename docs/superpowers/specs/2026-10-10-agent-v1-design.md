# Agent-supervised controller experiments — V1 specification

Status: written specification approved by the user after explanation; implementation plan pending review.

## Purpose and approved scope

Extend the existing triple-pendulum project with one experimental agent that
observes simulations, changes controller parameters, and evaluates the outcome.
The existing feedback controller still computes force at every integration step.
The agent only acts between experiments. Deliver a reproducible GitHub companion
with an honest baseline comparison, including unsuccessful experiments.

Use the current massive-rod model and local upright LQR recovery. Include an LLM
agent, four tools, a deterministic offline mode, objective metrics, JSONL logs,
held-out benchmarking, tests, and README instructions. Full recovery after a fall,
swing-up replanning, changes to the browser demonstration, hardware, and multiple
agents are outside V1. Improvement is an experimental result, not a guaranteed
acceptance criterion.

## Preservation and current state

- Repository: `LGOSSET-21/inverted-pendulum-control`.
- Original revision: `6f8576c51280a6453c36e10de592b7d4af18e20d`.
- Remote preservation branch: `baseline/pre-agent-v1`, verified at that revision.
- Local development branch: `feat/agent-v1`.
- Never force-push, merge into, or rewrite `main` as part of this work.
- `massive_rods.Model` already exposes dynamics, linearisation, and simulation.
  Reuse these equations instead of introducing another physical model.
- Keep existing entry points, saved trajectories, and visualizations compatible.

Initial verification: 24 Python tests passed in the full run; one test could not
load because Node was absent from PATH. That test passed separately with Node
configured. The massive-recovery JavaScript physics checks also passed. Run the
complete suite with the corrected environment for final validation.

## Simulation and controller interface

Add an isolated `src/agentic` package, callable using `PYTHONPATH=src`.
Its simulation interface accepts an eight-component SI initial state, controller
parameters, a finite-duration cart-force pulse, duration, and integration step.
Return time, states, applied controller force, external disturbance, and status.

Use `massive_rods.Model(rod_mass=0.01)` and the existing RK4 integration routine.
Default duration is 12 s and step is 0.0025 s. Saturate controller force at 8 N;
terminate at the original 60-degree tilt or 2 m track limits. Report nonfinite
states and integration failures as failed experiments, never successful results.
Require finite inputs, positive duration/step, consistent state shape, and pulse
boundaries on the integration grid; hold the pulse constant within each step.

Expose four positive scaling factors on the original LQR weights: cart position,
link angles, velocities (cart and angular), and control effort R. Each factor is
bounded to [0.1, 10]; all ones reproduce the original controller. Recompute the
Riccati solution and check closed-loop linear stability for every candidate.
These checks do not imply nonlinear or global stability.

## Metrics and selection objective

Report, with explicit units:

- Completion/failure status and simulated duration.
- Settling time after the pulse ends, or after initialisation when no pulse exists.
- Maximum absolute link angle, maximum absolute cart position, peak force,
  integrated squared controller force, and fraction of time at saturation.
- Constraint satisfaction and the aggregate candidate selection score.

Settled means all states remain within the existing thresholds through the end
of the run: cart position 0.02 m, cart speed 0.03 m/s, all angles 1 degree, and all
angular speeds 0.05 rad/s. Require at least one full second of observation after
settling. Missing settling is represented as null, never as zero or NaN.
Do not mistake an initially quiet period before a disturbance for recovery.

For tuning, rank candidates lexicographically by (1) number of failed or
unsettled scenarios, (2) number exceeding 0.5 m cart travel, and (3) mean normalized
cost. Per-scenario cost is settling time / 12 s + peak cart travel / 0.5 m +
force-squared integral / (8^2 * 12 s); missing settling contributes 1 to its time
term. Fixed failures/constraints take priority over this cost so early termination
cannot win by producing little measured effort. Preserve every raw metric.

## Four tools and one agent

1. `set_controller_parameters`: validate a complete candidate or bounded updates;
   return the effective parameters without changing the physics or limits.
2. `run_experiment`: evaluate the candidate on the fixed tuning suite and save
   trajectories plus metrics; return an experiment ID and summary.
3. `get_experiment`: retrieve parameters, metrics, and status for an experiment.
4. `compare_experiments`: compare recorded candidates with the fixed ranking.

The agent starts by evaluating the baseline and can use at most 12 candidate
evaluations, including baseline, and 60 tool calls per session by default.
Each candidate must run the complete tuning suite. The experiment store selects
the best measured candidate; untested LLM recommendations cannot become winners.
Tools accept only validated data and known experiment IDs, never executable code
or arbitrary filesystem paths. Invalid calls are logged and consume call budget.

The LLM backend uses an optional OpenAI dependency and an explicit model argument;
credentials come from the environment and are never saved. The agent receives
the objective, parameter bounds, tool schemas, and previous observations. Save
tool requests, results, and concise stated rationales, not private reasoning.
API failures preserve logs and stop with an explicit error; never silently
substitute the offline policy and label it an LLM run. Live model validation
depends on an available API credential; report any untested integration clearly.

The offline backend uses a deterministic, bounded coordinate search around the
best observed weights, accepting/rejecting changes from measured scores. It
exercises the same tools and logger without network access. Document it as an
adaptive search baseline, not evidence of LLM reasoning capability.

## Experiments and benchmark

Use four tuning scenarios: aligned +1-degree tilt, opposed (+1, -1, +1)-degree
tilts, a 3 N cart pulse over [4, 4.2) s from equilibrium, and 0.05 m initial cart
offset. Opposed tilts may fail; retain that outcome without weakening limits.

Use four separate validation scenarios: aligned -1.5-degree tilt, opposed
(-0.75, +0.75, -0.75)-degree tilts, a -2 N pulse over [5, 5.2) s, and -0.075 m
initial cart offset. These scenarios are evaluated only after selecting a
candidate on tuning results, and are not exposed to the tuning agent.

Benchmark the original controller and selected controller on every validation
scenario with identical integration settings. Include a seeded random-search
comparator over the same parameter bounds with the same candidate budget,
selected using tuning results only. Record each method's simulation count and
runtime; use one fixed seed for the minimal smoke benchmark and state that a
single run does not establish statistical superiority.

Produce machine-readable JSON and a compact Markdown table with failure counts,
settling times, displacement, and effort. Do not suppress regressions. Replay
the selected candidate with a halved integration step and report discrepancies.
The benchmark must run entirely offline; optional live LLM results are labeled
separately and include the model identifier and budget.

## Logging, files, and reproducibility

Create a new output directory for each run; never overwrite earlier runs.
Append JSONL events with UTC timestamps, experiment IDs, scenario definitions,
parameters, numerical settings, source Git revision/dirty flag, dependency
versions, policy/model and seed, tool calls, metrics, statuses, and errors.
Store trajectories locally using relative artifact paths. Serialize strict JSON
without NaN/Infinity. Exclude credentials and environment dumps. Keep generated
run directories out of Git; commit one compact, reproducible benchmark summary
with provenance, and document how to regenerate full logs.

Modules separate simulation, metrics, tools/store, agent policies, and benchmark
CLI. Add focused tests under `tests/` and a README section with installation,
offline and LLM usage, benchmark commands, expected artifacts, scientific limits,
and the preserved baseline link. Do not claim 20-degree recovery or successful
swing-up from local upright tuning.

## Acceptance and verification

- Default adapter matches the original massive-model aligned trajectory and
  metrics within numerical tolerance; original entry points still work.
- Tests exercise exact equilibrium, disturbances, uncompleted runs, invalid
  parameters, terminal limits, settling hold time, and scoring precedence.
- Agent tests use a scripted model transport to verify the tool loop, invalid
  calls, budgets, errors, and best-candidate selection without paid requests.
- Logging tests check valid JSON, reproducibility fields, unique run locations,
  and preservation of failed experiments.
- A real offline tuning and benchmark run completes and produces inspectable
  artifacts. Check validation scenarios are excluded from candidate selection.
- Run existing Python tests with Node available, affected JavaScript regression
  checks, new tests, and numerical refinement before publishing results.
- Publish work on a feature branch and open a draft PR with actual verification
  results and limitations; do not merge it into main.

## Specification self-review

Checked against the approved scope: single agent, four tools, massive rods,
local LQR, offline reproducibility, LLM support, metrics, logs, and benchmark.
No placeholder requirements remain. The baseline is a Git revision; benchmark
baseline is the original all-ones controller on the same physical model. These
two meanings are explicitly separated. The user approved continuation after
reviewing the specification summary; the next step is implementation-plan review.
