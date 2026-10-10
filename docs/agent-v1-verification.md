# Agent V1 verification record

- Original baseline: `6f8576c51280a6453c36e10de592b7d4af18e20d`, preserved on `baseline/pre-agent-v1`.
- Benchmark source: `e32af1cc6b26405528e23c4071fbd0446ff43275`, clean when started.
- Reviewed fixes: `f4837c9` (integer pulse-grid boundaries, interrupted-session finalization, extreme-input rejection).
- Environment: Python 3.9.7, NumPy 2.0.2, SciPy 1.13.1. Repository recommendation remains Python 3.11.
- Full final Python suite: **51 tests passed**, including 26 new agentic tests.
- Existing JavaScript suites passed: `test_massive_recovery_physics.cjs`, `test_massive_recovery_fall.cjs`, `test_massive_recovery_page.cjs`.
- Real offline benchmark: 12 adaptive candidates, 12 random candidates (seed 21), each including baseline; 96 tuning simulations, 12 validation simulations, 8 refinement simulations.
- No live API call was made: no API credential or OpenAI SDK was available in the test environment. Scripted transport tests cover the model/tool protocol and failure paths; they do not prove live service/model compatibility.

The benchmark was already running when independent review identified the grid
rounding and interruption issues. Its pulses use exact literal boundaries,
none of its runs were interrupted, and all initial states are within the final
input guard. After correction, the integer-grid pulse schedule was checked
against **all 116 saved trajectory disturbance arrays**, with exact equality.
The original trajectory-parity tests and full final test suite pass. Thus the
committed benchmark remains attributed to its actual source revision; it has
not been relabeled as a rerun of the fixed revision.

Independent review findings were reproduced before correction. A calculated
`0.1 + 0.2` pulse boundary now behaves like literal `0.3`. Ctrl-C preserves
completed and partial artifacts, excludes interrupted candidates from selection,
and exits with status 130. Extreme initial-state magnitudes above 1e6 SI are
rejected before numerical calculation. This guard is far outside the physical
operating range; it is not a stability claim.

The implementation retains the dedicated clone and feature branch approved for
this task rather than creating another checkout. Neither original physics code
nor browser artifacts were modified. No findings were deferred. Full local
trajectories/events are generated under ignored `runs/`; compact JSON and Markdown
results are committed under `results/agentic/`.
