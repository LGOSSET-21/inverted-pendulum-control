# Research log

## 14 September 2026 — First working cart-pole experiment

Created a separate project from pinn-hemodynamics. First milestone: nonlinear point-mass cart-pole, upright linearisation, state feedback by pole placement, actuator saturation and an offline English comparison with an unforced baseline.

Saved 14 trajectories: balance and positioning at 2, 5 and 10 degrees, plus a disturbance experiment starting at zero angle, each with and without feedback. Fixed controller poles: -1.4, -1.8, -2.2, -2.6 per second. Model and units are explicit in README.md. Full-state feedback is an ideal sensing assumption. No LQR, state observer, swing-up or hardware experiment is claimed.

Numerical verification covers equilibrium, linearisation, closed-loop eigenvalues, energy conservation, force saturation and time-step refinement. Browser interaction validation has not been performed: a previous browser-tool policy denied local file URLs. The page has no remote dependencies or server requirement.

## 16 September 2026 — Reproducible local environment

Installed NumPy 2.0.2 in the project-specific virtual environment and configured VS Code to use it. All four numerical tests passed. Regenerated all 14 trajectories; all seven controlled scenarios completed and settled. Checked the embedded JavaScript syntax and confirmed the unforced push experiment remains upright before the disturbance. Obsolete push experiments, if present, are retained in results/archive. Browser rendering remains unverified.

## 16 September 2026 — Pole placement versus LQR

Added two continuous-time LQR designs using Q = diag(10, 1, 100, 1), with R = 4 (gentle) and R = 0.1 (responsive). The existing pole-placement design is unchanged. Saved 28 trajectories: seven scenarios times four methods including the unforced baseline. Added a controller selector, four overlaid plot curves, and a comparison table reporting settling, peak actuator force and integral of force squared. All public explanations are in English.

All six numerical tests passed, including Riccati residual, positive definiteness, closed-loop poles, nonlinear LQR recovery and time-step refinement. Optimality is limited to the unconstrained linear design problem. Effort is not energy. Visual browser verification remains pending because of the earlier local-file policy restriction.

## 16 September 2026 — Double inverted pendulum

Added a separate English offline page, linked from the single-pendulum laboratory. The model uses two massless serial rods and two point masses, with both angles measured absolutely from upright. Total suspended mass and upright height match the single-link example; mass distribution differs. The six-state LQR is calculated afresh, with Q = diag(10,1,100,1,100,1), R = 0.1, and an 8 N actuator limit.

Saved six double-pendulum runs: aligned +3/+3 degrees, opposed +3/−3 degrees, and a 3 N push over 4.0–4.2 s from upright, each with and without feedback. Two single-pendulum comparison runs use matched initial aligned tilt or push and the same integration step. Full data are in results/double. This is an illustrative comparison of specified designs, not a universal ranking or global-stability claim.

Controlled outcomes: aligned settled at 2.56 s (peak 4.26 N); opposed settled at 3.0225 s (peak 8 N, actuator saturation reached); push settled at 6.1425 s from start (1.9425 s after the push ended, peak 4.16 N). Local stabilisation only; no swing-up, sensing noise or hardware claims.

Verification includes analytical versus numerical linearisation, controllability, Riccati residual, stable closed-loop poles, nonlinear recovery and integration-step refinement. A free-motion energy test at 0.001 s initially exceeded the strict 1e-8 J threshold (2.32e-8 J); halving the step reduced the error to 9.89e-10 J. The retained test checks both the strict refined error and convergence under refinement. Embedded page data and JavaScript syntax were checked. Visual browser verification remains pending under the earlier local-file restriction.

## 16 September 2026 — Playback fix and swing-up

Reproduced the first-frame failure in a JavaScript regression test: a timestamp slightly earlier than the click-time clock produced negative t; sample() then indexed row −1 and raised a TypeError. Both single- and double-pendulum pages now clamp negative elapsed time and protect the beginning of the sample array. The two-page regression passes. The double canvas now places the cart near the centre, allowing links below it to remain visible.

Added a start-from-bottom manoeuvre: exact initial state [0,0,π,0,π,0], five-second planned trajectory tracked by time-varying LQR, then upright LQR. SciPy 1.13.1 is installed in the project environment and listed in requirements. An initial high-resolution planning attempt was stopped because its iterative solver was too slow. The retained 61-node Hermite–Simpson plan reached the 400-evaluation budget with a 3.3e-6 maximum derivative defect, rather than a claim of objective optimality. Only independent nonlinear replay is published.

Nominal replay: upright settling by 5 s, maximum cart displacement 0.5279 m, peak actuator force 8 N, squared-force effort 41.1235 N²·s over 12 s. Uncontrolled baseline remains hanging. The scenario removes the near-upright tilt cutoff but retains the ±2 m travel cutoff. This is a nominal planned swing-up demonstration, not verified global feedback stabilisation. Browser rendering remains unverified under the earlier tool restriction.

Final verification: all three swing-up tests passed, including full-trajectory agreement after halving the integration step. JavaScript regression tests passed for both pages; an in-memory DOM/canvas harness exercised all four double-pendulum scenarios, both drawing paths, Play, Restart and timeline changes. These are code-level checks, not a claim of browser visual inspection.

## 17 September 2026 — Triple pendulum completed

Added the eight-state triple model, a new English standalone page and navigation from the single/double pages. Total suspended mass and upright height are unchanged (0.2 kg and 0.5 m), distributed over three equal point masses and rods. Analytic linearisation, mechanical power balance, controllability and continuous-time LQR are tested.

All four scenarios are saved with uncontrolled and controlled runs. Aligned +1° tilts settle in 2.1325 s. Opposed +1°/−1°/+1° tilts fail with saturated control, reaching the angle cutoff at 0.295 s; the page explicitly preserves that failure. The shared 3 N pulse settles at 6.3225 s from start. Its table includes the earlier single/double results while documenting model/objective differences.

Triple swing-up planning resumed the first 600-evaluation attempt (defect 0.0117523) for a second 600 evaluations, reaching a 0.0081123 collocation derivative defect. No claim of optimizer convergence or global optimality is made. The resulting six-second reference passes independent nonlinear replay with actual 8 N saturation: settling at 6.5 s, maximum cart displacement 0.7214 m, effort 46.4264 N²·s over 12 s. The uncontrolled baseline stays hanging.

Verification: all five triple numerical tests passed, including full-trajectory comparison after halving the integration step. The in-memory page test exercised all four scenarios, both canvas paths, first-frame timing and restart. Playback boundary regression passed for all three pages. Embedded datasets and the three-system pulse comparison were checked. These checks do not claim browser visual inspection, which remains unavailable under the earlier local-file tool restriction.

## 17 September 2026 — More faithful triple-pendulum rendering

Replaced unequal horizontal/cart and rod scales with a shared metre scale, fitted to all recorded joint positions and fixed for each scenario. Both comparison panels use the same world bounds. Added a rear guide rail, carriage, visible bearings, rigid coloured rods, a 0.10 m scale bar, a 0.7 s tip trace and a signed force arrow. The drawing planes are explained; physical contact remains unmodelled.

Playback now uses cubic Hermite interpolation of each generalised coordinate with its recorded velocity, leaving the datasets, forces, gains and metrics unchanged. Added 0.25x, 0.5x (default) and 1x playback. Rig drawing continues per animation frame; full plot redraws are limited to 12 Hz to reduce work per frame. No added oscillations or artificial smoothing of the physical trajectory.

Tests passed: first-frame/time boundaries on all three pages; all triple page handlers; exact constant-acceleration interpolation; rigid 1/6 m links; agreement of interpolated poses with the full-resolution numerical trajectories to within 0.001 in the respective coordinate units at tested intermediate samples. Actual visual browser rendering remains unverified under the earlier tool restriction.

## 17 September 2026 — Larger view and three trails

Expanded the triple-pendulum panels to full width with 560 px canvases, preserving the common physical metre scale. Added one-second fading trails for all three point masses in their respective colours. Physical trajectories and metrics are unchanged.

Triple page: removed the uncontrolled panel and corresponding angle curves at user request. Saved baseline data are retained; the display now focuses on controlled motion.

## 17 September 2026 — Live drag and automatic local recovery

Added live nonlinear integration and mouse/touch picking for all three point masses. A bounded spring/damper applies Cartesian force through the mass Jacobian; release removes it and the original saturated LQR continues balancing. Live mode starts upright and has a separate reset and explicit failure cutoffs. Recorded playback is retained in a collapsed section. No arbitrary-pull or global recovery guarantee is made.

Verified JavaScript/Python derivative agreement within 1e-8 on twelve sampled states, recovery after gentle pulls on all three joints, and pointer pick/drag/release/reset/cancel behaviour. Existing recorded-page handler tests also passed. Assets are embedded into the standalone generated HTML by the builder.

## 17 September 2026 — Unified interaction and explicit recovery assist

User rejected the separate live panel and limited local recovery. Removed that panel and integrated pointer capture into the original triple canvas. State and velocity are preserved exactly on grabbing; camera transform is unchanged. The same three trails continue during interaction, and playback can continue beyond 12 seconds for recovery.

Recovery assistance is explicitly a different model: ideal actuated joints with inverse-dynamics damped angle control, plus the cart mass equation under limited cart PD force. It is not claimed to be a more capable original LQR. The UI identifies assistance and hides recorded performance plots/metrics while it is active. Restart returns to recorded cart-only experiments.

Tests passed for assisted recovery on all three joints from hanging/upright/folded states; integrated grabs at 0, 3 and 12 seconds, no position/velocity or camera jump, release recovery and restart; existing playback boundaries and scenario handlers. Browser visual verification remains unperformed.

## 17 September 2026 — Restore physical, underactuated interaction

User correctly rejected ideal joint assistance as inconsistent with the intended project. Removed it from the generated page and archived the superseded engine/tests. The integrated canvas now uses the original nonlinear mass matrix, free hinges, fixed rod lengths and only the cart motor. The mouse is an external spring/damper force mapped by JᵀF, not inverse kinematics or motor torques. Release leaves the state untouched; a fall is permitted.

Exported the existing swing-up tracking schedule for live cart-only continuation, then upright LQR after 6 seconds. Cart command is saturated at 8 N; the pulse scenario retains its external disturbance. Fixed-step RK4 uses 0.00125 s, with a 2 m travel cutoff. Recorded metrics are hidden after manipulation.

Verified 24 random force/transmission cases across all three points against independent Python mass-matrix/Jacobian calculations, including mechanical power balance to 1e-7. Gentle release recovery and integrated pointer continuity passed. The superseded assistance claims earlier in this chronological log describe rejected work, not the current model.

## 17 September 2026 — Diagnose runaway after dragging

Reproduced one-second 0.1 m cursor offsets: the unsupervised local LQR saturated for approximately 2.94–2.99 seconds and, in an uncropped three-second test, drove the cart beyond 9 m. A separate test showed nonzero saturated force for states physically equivalent to upright but offset by full angle turns.

Corrected angular tracking errors modulo 2π and introduced smooth local-feedback authority with cart-only braking outside its envelope. No joint motors or geometric state correction were introduced. Preserved cursor picking offsets, ramped the tether on over 0.08 s, and filtered cursor targets over 0.05 s. Live UI distinguishes balancing from limited cart braking; stored experiment data remain unchanged.

Regression checks pass for the reproduced sustained-pull cases (cart stays inside 2 m during the five-second test), full-turn equivalent states, gentle recovery on each point, and undisturbed swing-up continuation at 0/3/5 s. Mechanical force/power balance still matches the independent Python model. This is a bounded set of tests, not a global recovery guarantee.

## 17 September 2026 — Automatic cart-only recovery sequence

User correctly noted that merely reducing LQR authority does not bring a fallen pendulum upright. Added a hybrid recovery controller: damp towards the downward equilibrium, stabilise there with a separately designed cart-only LQR, and restart the existing six-second swing-up reference after strict readiness tolerances hold for 0.25 s. Switching changes control laws only, never the state. Force is capped at 8 N and travel retains the 2 m cutoff.

Verified recovery after one-second 0.1 m target-offset pulls on all three points: 25.30/35.59/31.75 simulated seconds, peak travel 0.717/0.717/0.956 m, with finite states and no resets. Integrated pointer tests also passed. An earlier, more sensitive fallback trigger was tried but lengthened these recovery trials; retained trigger is tracking authority < 0.1 for 0.15 s. This is a tested hybrid strategy, not a global stability proof.

Default viewing speed is now 1x, with 2x available. Status explicitly shows damping versus raising again, so settling downward is not mistaken for a completed recovery.

## 18 September 2026 - English scientific brief

Created a five-page illustrated PDF for discussing this learning project with a Control Principles professor. Figures use the saved triple-link CSV trajectory. Recomputed controllability rank 8, the LQR gain and closed-loop poles, and relative CARE residual 2.33e-10. All 19 Python unit tests passed. The brief distinguishes saved benchmark results from live mouse interaction and states saturation, local-stability and physical-model limitations. No hardware validation or global recovery claim is made.

## 24 September 2026 — Uniform massive rods, near-upright stage

Added a separate model with 10 g uniformly distributed along each rod, retaining the endpoint masses (suspended total 230 g). Included centre-of-mass translation, central rotational inertia mL²/12 and gravity. Recalculated upright linearisation and LQR with unchanged Q, R and ±8 N limit. Zero rod mass recovers the original model.

Six matched trials compare the zero-mass and massive-rod variants in the same solver. Massive rods: aligned 1° lean settles at 2.1225 s, peak force 2.2073 N; a 3 N push ends at 4.2 s and settling occurs at 6.3200 s absolute time, peak 4.1839 N. Opposed angles fail at the tilt cutoff, 0.28875 s; the refined stop time is 0.288125 s. No universal stability improvement is inferred.

The first opposed-angle refinement exceeded the chosen 0.002 per-state numerical comparison bound, so its integration step was halved to 0.00125 s and checked at 0.000625 s. Matched state differences then passed; aligned and push discrepancies stayed below 6e-7 in their respective state units. All 23 Python tests passed (394 s), including four new physical-model tests. Node checks of the new page's drawing, playback, scenario switching, scrubbing and restart passed; these do not constitute browser visual inspection.

New English page: visualization/massive-rods.html. Derivation: docs/massive-rods.md. CSVs and checks: results/massive_rods/. Original demo and professor package remain unchanged. Massive-rod swing-up and mouse interaction are pending separate follow-up work; the old swing-up trajectory was not reused.

## 24 September 2026 — Massive-rod swing-up and redesigned playback

Re-optimised an 81-node, six-second reference using the massive-rod equations (10 g added to each rod), starting from the old reference only as an initial guess. Retained ±7.5 N planning bounds and ±8 N motor limit. After 600 optimiser evaluations, maximum derivative defect was 0.006106; the budget was reached, so no optimality claim is made.

Independent nonlinear forward replay starts exactly hanging at rest, tracks with newly computed time-varying LQR, and switches to massive-model upright LQR at 6 s. It settles at 6.380 s; peak force 8 N, maximum cart excursion 0.721004 m. At integration steps 0.00125 and 0.000625 s, settling times agree and maximum angular discrepancy stays below 6.29e-7 rad. Full state discrepancy and CSV are saved under results/massive_rods/.

Created visualization/massive-swingup.html with embedded data, a larger single scene, three joint trails, force arrow, motor and position readouts, phase labels, slow playback and scrubbing. Fixed-length rods are reconstructed from Hermite-interpolated generalised coordinates. No forces or geometric corrections are introduced by display smoothing. The stage-1 comparison links to this new page. Mouse dragging is still pending for the massive model; original massless pages and professor package are unchanged.

All 25 Python tests passed (234 s). New batch/scalar and hanging-equilibrium checks pass. Node page checks verify playback, scrubbing, restart, finite interpolation and invariant rod lengths; local links pass. These automated canvas-handler checks do not constitute visual browser inspection. Documentation records assumptions, result values and reproduction commands.
