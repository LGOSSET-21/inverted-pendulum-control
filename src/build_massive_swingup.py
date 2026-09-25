"""Validate massive-rod swing-up and publish a standalone English playback."""
import json
from pathlib import Path
import numpy as np
from massive_swingup import simulate,tracker
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'results/massive_rods'
rows,m=simulate(dt=.00125);fine,fm=simulate(dt=.000625)
if m['status']!='completed' or m['settling_s'] is None:raise RuntimeError(f'Unsuccessful replay: {m}')
if fm['status']!='completed' or fm['settling_s'] is None:raise RuntimeError(f'Unsuccessful refined replay: {fm}')
errors=np.max(abs(rows[:,1:9]-fine[::2,1:9]),axis=0)
assert np.max(errors)<.01,errors
assert abs(rows[:,9]).max()<=8.0000001
assert abs(rows[:,1]).max()<2
np.testing.assert_allclose(rows[0,1:9],[0,0,np.pi,0,np.pi,0,np.pi,0],atol=1e-12)
m.update(max_cart_displacement_m=float(abs(rows[:,1]).max()),refinement_per_state_max_error=errors.tolist(),refined_settling_s=fm['settling_s'],integration_step_s=.00125,force_limit_N=8,rod_mass_kg=.01)
np.savetxt(out/'swingup_lqr.csv',rows,delimiter=',',header='time,x,v,theta1,omega1,theta2,omega2,theta3,omega3,force,push',comments='')
(out/'swingup_validation.json').write_text(json.dumps(m,indent=2))
display=rows[::16].tolist()
if display[-1][0]!=rows[-1,0]:display.append(rows[-1].tolist())
payload={'rows':display,'metrics':m}
template=(ROOT/'visualization/templates/massive-swingup.html.in').read_text()
(ROOT/'visualization/massive-swingup.html').write_text(template.replace('__SIMULATION__',json.dumps(payload)))
print(json.dumps(m,indent=2),flush=True)
