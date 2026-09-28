# Interactive massive-rod recovery

The [live demonstration](../visualization/massive-recovery.html) integrates the nonlinear massive-rod model in the browser. It is the main interactive page; the [massless-rod reference](../visualization/triple.html), [near-upright model comparison](../visualization/massive-rods.html) and [recorded massive-rod swing-up](../visualization/massive-swingup.html) remain separate and unchanged.

## Interaction

Choose an upright scenario and grab a coloured endpoint. Move the pointer a little to apply a small force; move further and hold to challenge the controller. Release to remove the hand force without resetting angles or velocities. The arrow and “Hand” readout show the Cartesian force applied to the selected mass. The mouse commands a force, not a rigid position constraint.

Screen displacement is measured relative to the initial grab, with a 2 px dead zone. Beyond this, displacement `d` in pixels commands a force magnitude `min(0.4, 0.00008*d + 0.000012*d*d)` N, in the pointer-displacement direction. A first-order filter with a 0.12 s time constant smooths engagement. Release removes the force immediately. There is no imposed angular displacement, angle clamp or artificial damping of the held joint.

The force enters the nonlinear equations as `J(q)^T F`, where `J` is the selected endpoint's Cartesian position Jacobian. It acts in all controller phases. An actual pull interrupts swing-up; a stationary click does not. Pause, pointer cancellation, loss of capture and window blur end the interaction.

## Model and control

The model retains a 0.8 kg cart, three endpoint masses of 0.2/3 kg, three uniform 10 g rods of length 1/6 m, gravity 9.81 m/s² and cart viscous friction 0.08 N·s/m. RK4 uses a fixed step of 0.00125 s. See the [massive-rod derivation](massive-rods.md).

- Upright LQR controls the cart, with force saturation at ±8 N.
- Losing upright balance (any wrapped angle over 0.95 rad or cart displacement over 1.05 m) selects hanging recovery. This is a controller switch, not a reset or a physical collision.
- Far from hanging, the cart is gently centred and braked. Near hanging, a downward-equilibrium LQR damps the motion.
- After release, swing-up is allowed only when every downward angle error is below 0.5°, every angular speed below 0.02 rad/s, cart displacement below 0.015 m and cart speed below 0.02 m/s continuously for 0.8 s.
- The controller tracks the embedded massive-rod trajectory using a 0.01 s time-varying LQR schedule, then returns to upright LQR. No state reset occurs at either handoff.

This is a numerical educational model, not a hardware-validated system or global recovery guarantee. The rail is a visual guide with no end-stop collision model; extreme pulls may move the cart outside the view. The pre-existing opposing-angle initial trial (+1°/−1°/+1°) may lose balance before recovering. The saved-experiment settling times in the README do not apply to arbitrary live interactions.

## Display

Trails and plots sample the live state at 50 Hz. The plots keep the last 20 s; the trails keep about 1.3 s. Pause freezes the data and Reset clears it. The angle plot shows angles from the upward vertical, wrapped to ±180°, breaking lines across wrapping discontinuities. Coincident traces can hide beneath the yellow trace, which is drawn last; the page explains this. The force plot shows cart input, not hand force.

## Verification and maintenance

The page is self-contained and hand-maintained. Existing page generators rebuild the recorded demonstrations; they do not overwrite this page. The embedded reference and gains originate from the massive-rod prototype's verified 0.01 s schedule. The JavaScript model and controller functions are retained from the user-validated local prototype.

Run from the repository root, using Node 20+ with no npm dependencies:

```sh
node tests/test_massive_recovery_physics.cjs
node tests/test_massive_recovery_fall.cjs
node tests/test_massive_recovery_page.cjs
```

The harness executes the actual page script, replacing only browser drawing, DOM surfaces and animation scheduling. Tests check small-pull rejection, strong-pull loss of balance, mechanical power balance using independently assembled body energies, open-loop falling, exact zero-click equivalence, continuity on release, repeated gestures, pointer ownership, pause/reset, and the full fall → hanging → swing-up → upright sequence for all three masses. Display sampling and pause/reset are checked separately from dynamics. Existing Python and JavaScript suites continue to cover the saved experiments and original massless model.

These tests are numerical and browser-handler tests, not a substitute for inspecting the full layout and pointer interaction in a real browser. The local canvas drawings were additionally rendered offline during development.
