"""Reproduce the worked example, data, tables and three supplement figures."""
from pathlib import Path
from dataclasses import asdict
import argparse,json,platform,hashlib
import numpy as np
import pandas as pd
import scipy
import matplotlib.pyplot as plt
from model import Settings,simulate,analyse,bootstrap,truth
from plots import relationship_plot,components_plot,diagnostics_plot
ROOT=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bootstrap',type=int,default=500)
    parser.add_argument('--seed',type=int,default=20261005)
    parser.add_argument('--quartic',type=float,default=0)
    parser.add_argument('--output',type=Path,default=ROOT/'results')
    args=parser.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
    s=Settings(seed=args.seed,quartic=args.quartic);data,A=simulate(s)
    fit=analyse(data);boot=bootstrap(data,fit,args.bootstrap,seed=args.seed+1)
    data.to_csv(out/'observed_data.csv',index=False,float_format='%.12g')
    pd.DataFrame({'id':data['id'],'true_breeding_value':A}).to_csv(out/'simulation_truth.csv',index=False,float_format='%.12g')
    boot['draws'].to_csv(out/'bootstrap_draws.csv',index=False,float_format='%.12g')
    values=truth(s)
    rows=[]
    for k in ['b','H','G','V_lin','V_quad','A_g']:
        ci=boot['intervals'].get(k,[None,None])
        rows.append(dict(quantity=k,truth=values[k],estimate=fit['estimate'][k],lower=ci[0],upper=ci[1],naive=fit['naive'][k]))
    pd.DataFrame(rows).to_csv(out/'estimates.csv',index=False,float_format='%.10g')
    higher=analyse(data,order=81,sensitivity=False)
    checks={k:abs(higher['estimate'][k]-fit['estimate'][k]) for k in ['b','H','A_g']}
    summary=dict(settings=asdict(s),truth=values,estimate=fit['estimate'],naive=fit['naive'],
                 alternative=fit['alternative_share'],delta_aic=fit['delta_aic'],intervals=boot['intervals'],
                 bootstrap_replicates=args.bootstrap,bootstrap_failed=boot['failed'],bootstrap_boundary=boot['boundary_count'],
                 integration={name:{k:fit[name][k] for k in ['order','checked_order','boundary']} for name in ['fit','alternative']},
                 quadrature_change=checks,zero_count=int((data.offspring==0).sum()),
                 versions=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),
                 observed_data_sha256=hashlib.sha256((out/'observed_data.csv').read_bytes()).hexdigest())
    (out/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    for filename,figure in [('case1_relationship',relationship_plot(data,s,fit)),
                            ('case2_components',components_plot(s,fit,boot)),
                            ('case3_diagnostics',diagnostics_plot(fit))]:
        figure.savefig(out/(filename+'.pdf'));figure.savefig(out/(filename+'.png'),dpi=160);plt.close(figure)
    # Numbers in the typeset supplement are generated from this same result.
    table=['\\begin{tabular}{lrrrr}\\toprule','Quantity & Generating value & Estimate & 95\\% lower & 95\\% upper \\\\ \\midrule']
    names={'b':r'$b$','H':r'$H$','G':r'$G$','V_lin':r'$V_{\rm lin}$','V_quad':r'$V_{\rm quad}$','A_g':r'$\mathcal A_g$'}
    for row in rows:table.append(names[row['quantity']]+' & '+' & '.join(f"{row[k]:.4f}" if row[k] is not None else '---' for k in ['truth','estimate','lower','upper'])+r' \\')
    table += [r'\bottomrule\end{tabular}']
    (out/'estimates_table.tex').write_text('\n'.join(table)+'\n')
    macros={'EstimatedShare':fit['estimate']['A_g'],'NaiveShare':fit['naive']['A_g'],'EstimatedG':fit['estimate']['G'],
            'EstimatedE':fit['estimate']['E'],'EstimatedReliability':fit['estimate']['reliability'],'AICDifference':fit['delta_aic']}
    (out/'numbers.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+f'{v:.4f}'+'}' for k,v in macros.items())+'\n'+
        '\\newcommand{\\ZeroCount}{'+str(summary['zero_count'])+'}\n'+
        '\\newcommand{\\BootstrapCount}{'+str(args.bootstrap)+'}\n'+
        '\\newcommand{\\BootstrapFailures}{'+str(len(boot['failed']))+'}\n')
    print(json.dumps({k:summary[k] for k in ['estimate','intervals','bootstrap_replicates','bootstrap_failed','quadrature_change']},indent=2))

if __name__=='__main__':main()
