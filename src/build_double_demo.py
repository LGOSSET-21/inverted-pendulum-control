"""Generate a self-contained double-pendulum page and full-resolution CSVs."""
from pathlib import Path
from dataclasses import asdict
import json
import numpy as np
import double_pendulum as double
from pendulum import simulate as single_simulate
ROOT=Path(__file__).resolve().parents[1]

def main():
    out=ROOT/'results/double';out.mkdir(exist_ok=True)
    package=dict(parameters=asdict(double.P),gain=double.controller()[0].tolist(),Q=double.Q.tolist(),R=double.R,cases={})
    for case in ['aligned','opposed','push']:
        runs={}
        for key,controlled in [('open',False),('lqr',True)]:
            data,metrics=double.simulate(case,controlled)
            np.savetxt(out/f'{case}_{key}.csv',data,delimiter=',',header='time_s,x_m,v_m_s,theta1_rad,omega1_rad_s,theta2_rad,omega2_rad_s,force_N,push_N',comments='')
            idx=list(range(0,len(data),8))
            if idx[-1]!=len(data)-1:idx.append(len(data)-1)
            runs[key]=dict(data=data[idx].round(8).tolist(),metrics=metrics)
        # Matched total suspended mass, height, initial aligned angle and push.
        # Different mass distributions/controllers mean this is illustrative.
        if case!='opposed':
            data,m=single_simulate(0 if case=='push' else 3,'push' if case=='push' else 'balance',method='responsive',dt=.0025)
            np.savetxt(out/f'{case}_single_lqr.csv',data,delimiter=',',header='time_s,x_m,v_m_s,theta_rad,omega_rad_s,force_N,push_N',comments='')
            runs['single']=m
        package['cases'][case]=runs
        print(case,runs['lqr']['metrics'])
    # Swing-up is validated by physical replay before its data are published.
    from swingup import simulate as swing_simulate
    runs={}
    for key,enabled in [('open',False),('lqr',True)]:
        data,metrics=swing_simulate(enabled)
        if enabled and (metrics['status']!='completed' or metrics['settling_s'] is None):
            raise RuntimeError('Swing-up physical replay failed: '+str(metrics))
        np.savetxt(out/f'swingup_{key}.csv',data,delimiter=',',header='time_s,x_m,v_m_s,theta1_rad,omega1_rad_s,theta2_rad,omega2_rad_s,force_N,push_N',comments='')
        idx=list(range(0,len(data),8))
        if idx[-1]!=len(data)-1:idx.append(len(data)-1)
        runs[key]=dict(data=data[idx].round(8).tolist(),metrics=metrics)
    package['cases']['swingup']=runs
    print('swingup',runs['lqr']['metrics'],flush=True)
    (out/'experiments.json').write_text(json.dumps(package,indent=2),encoding='utf-8')
    template=(ROOT/'visualization/double.html.in').read_text(encoding='utf-8')
    (ROOT/'visualization/double.html').write_text(template.replace('__DATA__',json.dumps(package,separators=(',',':'))),encoding='utf-8')
if __name__=='__main__':main()
