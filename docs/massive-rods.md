# Massive rods — near-upright study

This is an additive extension, not a replacement of the original massless-rod demonstration. Each of the three uniform rigid rods gains 0.010 kg; endpoint masses remain 0.2/3 kg each. Suspended mass therefore rises from 0.200 to 0.230 kg. Lengths remain 1/6 m. The cart stays at 0.8 kg and the actuator at ±8 N.

## Derivation

Let p_i be endpoint mass, r_i rod mass and l_i length. Angles are absolute from the upward vertical. Define D_i = sum(p_k, k ≥ i) + sum(r_k, k > i). Then:

- H_i = l_i (D_i + r_i/2).
- C_ii = l_i² (D_i + r_i/3).
- C_ij = l_i H_j for i < j, with symmetry for i > j.
- M_00 = cart mass + sum(p_i + r_i).
- M_0i = H_i cos(θ_i).
- M_ij = C_ij cos(θ_i − θ_j).

The one-third factor includes both translation of the rod centre and rotation about its centre, with I_c = r_i l_i²/12. Potential energy is g sum(H_i cos θ_i). Kinetic energy is ½ q̇ᵀ M q̇. The nonlinear equations use the associated centrifugal coupling, gravity, cart force and viscous cart friction. There are no joint motors.

A and B are recalculated at the upright equilibrium. Both models use Q = diag(10,1,100,1,100,1,100,1), R = 0.1, and their own Riccati solution. Thus this compares models with recalculated feedback, not a single fixed controller's robustness to unknown mass.

## Experiments

Aligned (+1°, +1°, +1°), opposed (+1°, −1°, +1°), and an external 3 N cart push from 4 to 4.2 s. Both mass settings run through the same solver. The external pulse is held on each integration interval, including RK4 substeps; the older generator uses a time-based endpoint evaluation, so small differences from old published push results are possible. Old saved results are untouched.

RK4 steps: 0.0025 s and 0.00125 s for aligned/push cases; 0.00125 s and 0.000625 s for opposed angles, where saturation makes numerical accuracy more sensitive. Force feedback is evaluated at the RK stages (ideal continuous state feedback). Trials retain 60° tilt and ±2 m track cutoffs; no contact model is implied. For stopped runs, refinement is compared over common times; status and both stop times are recorded. A stopped failure is not a successful stabilisation.

## Checks

The zero-rod-mass model recovers the original dynamics. Independent Cartesian centre-of-mass velocities and rod moments of inertia reconstruct the energy, separately from the matrix formula. Tests check mechanical power balance, positive mass-matrix eigenvalues at sampled configurations, finite-difference linearisation, stable closed-loop poles, and aligned recovery under time-step refinement. The generator checks refinement of all six trials and exports numerical diagnostics.

Open `visualization/massive-rods.html`. Reproduce with `python src/build_massive_rods.py`; run tests with `python -m unittest discover -s tests -q`. Data and diagnostics are in `results/massive_rods/`.

The near-upright stage described above does not include mouse interaction. Stage 2 below adds a recomputed swing-up from below. The original `triple.html` still uses massless rods. No old swing-up reference is reused for the new model. Ideal sensing/actuation, rigid rods, frictionless joints, and absence of collisions remain limitations. AI-assisted numerical study, without hardware validation.

## Stage 2 — Planned swing-up with massive rods

The 10 g rods now have a separate six-second swing-up reference. `plan_massive_swingup.py` uses the old massless reference only as an initial guess, then evaluates and optimises the defects using the massive-rod model. Eighty-one Hermite–Simpson nodes, ±7.5 N nominal force and ±1.7 m node bounds are retained. After 600 optimiser evaluations, maximum derivative defect is approximately 0.006106. The optimisation stopped at its evaluation budget; neither global optimality nor exact collocation feasibility is asserted.

`massive_swingup.py` reconstructs a Hermite reference using the massive-rod derivatives. A backward discrete Riccati recursion creates time-varying tracking gains. The plant is then integrated independently from exactly [0,0,π,0,π,0,π,0], with commanded force clipped at ±8 N. At six seconds, feedback changes to the recalculated upright LQR. The saved plan is not substituted for simulated states.

`build_massive_swingup.py` requires successful settling and replay agreement at integration steps 0.00125 s and 0.000625 s before creating the page. Per-state discrepancies, settling, peak force and cart excursion are saved in `results/massive_rods/swingup_validation.json`. These checks cover the nominal manoeuvre, not arbitrary drag recovery or uncertain hardware.

Reproduce in order:

```bash
python src/plan_massive_swingup.py  # optional if the saved massive reference is retained
python src/build_massive_swingup.py
python -m unittest discover -s tests -q
```

Open `visualization/massive-swingup.html`. It embeds its saved display data and works offline. Playback uses cubic Hermite interpolation of generalised positions and their velocities; fixed-length rods are reconstructed geometrically from angles. Deterministic trails follow the last 0.8 s of the same trajectory. Force arrows and colours are illustrative. Mouse dragging remains future work for the massive model. The original model, demo and professor package have not been replaced.

### Measured swing-up result

Nominal 12 s replay completes. Settling is reached at 6.380 s, with peak motor force 8.000 N and maximum cart excursion 0.721004 m. The refined run reaches the same settling time. Maximum coarse/fine discrepancies: cart position 2.13e-6 m, cart speed 6.98e-6 m/s, angles below 6.29e-7 rad, angular speeds below 4.62e-5 rad/s. These are numerical agreement checks within this model, not hardware error bounds.
