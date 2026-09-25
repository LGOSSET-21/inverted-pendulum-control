"""Build the offline English demo and save the numerical experiments."""
from pathlib import Path
from dataclasses import asdict
import json
import numpy as np
from pendulum import P,POLES,controller,linear_model,simulate,lqr_controller,LQR_WEIGHTS
ROOT=Path(__file__).resolve().parents[1]
def main():
    cases=[];K=controller();A,B=linear_model()
    for task in ['balance','position','push']:
        for tilt in ([0] if task=='push' else [2,5,10]):
            case=dict(task=task,tilt=tilt,target=.5 if task=='position' else 0.,runs={})
            for name in ['open','feedback','gentle','responsive']:
                data,metrics=simulate(tilt,task,name!='open',method='feedback' if name=='open' else name)
                np.savetxt(ROOT/'results'/f'{task}_{tilt}deg_{name}.csv',data,delimiter=',',header='time_s,x_m,v_m_s,theta_rad,omega_rad_s,controller_force_N,disturbance_N',comments='')
                indices=list(range(0,len(data),4))
                if indices[-1]!=len(data)-1:indices.append(len(data)-1)
                case['runs'][name]=dict(data=data[indices].round(7).tolist(),metrics=metrics)
            cases.append(case)
    package=dict(parameters=asdict(P),gain=K.tolist(),poles=POLES.tolist(),open_poles=np.linalg.eigvals(A).real.tolist(),cases=cases, lqr={name: dict(gain=lqr_controller(name)[0].tolist(), Q=weights[0], R=weights[1]) for name,weights in LQR_WEIGHTS.items()})
    (ROOT/'results/experiments.json').write_text(json.dumps(package,indent=2))
    source=(ROOT/'visualization/demo.html.in').read_text()
    (ROOT/'visualization/index.html').write_text(source.replace('__DATA__',json.dumps(package,separators=(',',':'))),encoding='utf-8')
    print('Saved 28 runs and visualization/index.html')
    for c in cases: print(c['task'],c['tilt'],c['runs']['feedback']['metrics'])
if __name__=='__main__':main()
