# Agent V1 — held-out benchmark

One deterministic run and one random-search seed; no statistical superiority claim.
Offline means adaptive coordinate search, not an LLM. Failures remain in the table.

Source revision: `e32af1cc6b26405528e23c4071fbd0446ff43275`; dirty: False.
Random seed: 21. Baseline has no search; candidate counts include the original controller.

| Method | Candidates | Tuning failed/unsettled | Validation failed/unsettled | Validation travel violations | Validation cost |
|---|---:|---:|---:|---:|---:|
| baseline | 0 | — | 1 | 0 | 0.5422 |
| offline | 12 | 1 | 1 | 0 | 0.4691 |
| random | 12 | 1 | 1 | 0 | 0.4471 |

| Method | Scenario | Status | Settling after disturbance (s) | Peak cart (m) | Effort (N²s) |
|---|---|---|---:|---:|---:|
| baseline | validation_aligned | completed | 2.4450 | 0.0637 | 0.2610 |
| baseline | validation_opposed | tilt_limit | — | 0.1507 | 18.7297 |
| baseline | validation_push | completed | 1.6400 | 0.0246 | 0.9117 |
| baseline | validation_offset | completed | 2.0300 | 0.0777 | 0.0169 |
| offline | validation_aligned | completed | 1.7850 | 0.0525 | 0.5823 |
| offline | validation_opposed | tilt_limit | — | 0.1102 | 18.0247 |
| offline | validation_push | completed | 0.5125 | 0.0133 | 0.8773 |
| offline | validation_offset | completed | 1.7525 | 0.0806 | 0.0990 |
| random | validation_aligned | completed | 2.0075 | 0.0562 | 0.7283 |
| random | validation_opposed | tilt_limit | — | 0.0727 | 17.7711 |
| random | validation_push | completed | 0.1300 | 0.0062 | 0.8062 |
| random | validation_offset | completed | 1.8875 | 0.0788 | 0.0846 |

## Numerical refinement

Selected controllers are replayed at dt/2. State error is measured on the common time interval.
Warning threshold: >0.01 in any SI state component, completion-status disagreement, or settling-presence disagreement.

| Method | Scenario | Max state difference | Settling difference (s) | Warning |
|---|---|---:|---:|---|
| offline | validation_aligned | 1.09126e-06 | 0.0012499999999999734 | False |
| offline | validation_opposed | 0.00223708 | None | False |
| offline | validation_push | 4.38495e-07 | 0.0 | False |
| offline | validation_offset | 4.51958e-07 | 0.0012499999999999734 | False |
| random | validation_aligned | 0.000138926 | 0.0 | False |
| random | validation_opposed | 0.00440351 | None | False |
| random | validation_push | 4.50027e-06 | 0.0012499999999997513 | False |
| random | validation_offset | 8.29998e-06 | 0.0012499999999999734 | False |

## Accounting

Simulation counts: `{"tuning_simulations": 96, "imported_tuning_simulations": 0, "validation_simulations": 12, "refinement_simulations": 8}`.
Runtime and chosen parameter factors are in benchmark.json. Full events and trajectories are in the generated run directory.
Peak angle/force, saturation, constraints, and failure details are retained in JSON.
This is local simulated recovery; it is not a swing-up or hardware result.
