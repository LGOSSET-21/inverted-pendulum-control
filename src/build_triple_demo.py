"""Publish validated triple-pendulum simulations to a standalone English page."""
from pathlib import Path
import json
import numpy as np
import triple_pendulum as model
ROOT=Path(__file__).resolve().parents[1]
HEADER='time_s,x_m,v_m_s,theta1_rad,omega1_rad_s,theta2_rad,omega2_rad_s,theta3_rad,omega3_rad_s,force_N,push_N'

def main():
    out=ROOT/'results/triple';out.mkdir(exist_ok=True)
    D=dict(gain=model.controller()[0].tolist(),Q=model.Q.tolist(),R=model.R,cases={})
    for case in ['aligned','opposed','push','swingup']:
        if case=='swingup':
            if not (out/'swingup_reference.npz').exists():continue
            from triple_swingup import simulate
        else:simulate=lambda enabled:model.simulate(case,enabled)
        runs={}
        for key,enabled in [('open',False),('lqr',True)]:
            data,m=simulate(enabled)
            if case=='swingup' and enabled and (m['status']!='completed' or m['settling_s'] is None):
                raise RuntimeError('Swing-up replay not validated: '+str(m))
            np.savetxt(out/f'{case}_{key}.csv',data,delimiter=',',header=HEADER,comments='')
            idx=list(range(0,len(data),8))
            if idx[-1]!=len(data)-1:idx.append(len(data)-1)
            runs[key]=dict(data=data[idx].round(8).tolist(),metrics=m)
        D['cases'][case]=runs;print(case,runs['lqr']['metrics'],flush=True)
    # Existing pulse runs have the same 3 N input, duration and integration step.
    prior=ROOT/'results/double/experiments.json'
    if prior.exists():
        previous=json.loads(prior.read_text())['cases']['push']
        single=previous['single']
        D['push_comparison']=[dict(name='Single · responsive LQR',status=single['status'],settling_s=single['settling_time_s'],peak_force_N=single['peak_force_N'],effort_N2s=single['force_squared_integral_N2s']),dict(name='Double · LQR',**previous['lqr']['metrics'])]
    from triple_swingup import tracker
    D['tracking']=tracker()[0].schedule
    D['downGain']=model.down_controller()[0].tolist()
    (out/'experiments.json').write_text(json.dumps(D,indent=2))
    html=(ROOT/'visualization/triple.html.in').read_text().replace('__DATA__',json.dumps(D,separators=(',',':')))
    html=html.replace('__LIVE_PHYSICS__',(ROOT/'visualization/live-physics.js').read_text()).replace('__LIVE_INTERACTION__',(ROOT/'visualization/live-interaction.js').read_text())
    html=html.replace('__RECOVERY_CONTROL__',(ROOT/'visualization/recovery-control.js').read_text())
    (ROOT/'visualization/triple.html').write_text(html,encoding='utf-8')
if __name__=='__main__':main()
