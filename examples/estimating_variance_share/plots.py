"""Shared plotting functions for the paper supplement and the Shiny app."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from model import conditional_prediction, truth
BLUE='#2166ac';ORANGE='#b35806';GREY='#727272'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                     'axes.spines.right':False,'pdf.fonttype':42,'savefig.bbox':'tight'})

def relationship_plot(data, settings, fitted, A=None):
    """Separate observed noisy predictors from the conditional breeding-value curve."""
    cal=fitted['calibration'];e=fitted['estimate']
    fig,axes=plt.subplots(1,2,figsize=(10,3.8),layout='tight')
    x=cal['averages'];axes[0].scatter(x,cal['W'],s=8,color=GREY,alpha=.3,rasterized=True)
    pred=conditional_prediction(cal,fitted['fit'])[0];idx=np.argsort(x)
    axes[0].plot(x[idx],pred[idx],color=BLUE,lw=2,label='Fitted mean given height measurements')
    axes[0].set(xlabel='Mean observed height deviation (cm)',ylabel='Surviving offspring',title='a  What is observed')
    axes[0].legend(frameon=False,fontsize=8)
    grid=np.linspace(-3.2*np.sqrt(settings.G),3.2*np.sqrt(settings.G),250)
    actual=np.exp(np.log(settings.mean_output)+settings.b*grid+.5*settings.H*grid**2-settings.quartic*grid**4)
    z=grid-e['mu'];pred=np.exp(e['alpha']+e['b']*z+.5*e['H']*z*z)
    axes[1].plot(grid,actual,color=GREY,ls='--',label='Generating relationship')
    axes[1].plot(grid,pred,color=BLUE,label='Estimated relationship')
    axes[1].set(xlabel='Breeding value (cm)',ylabel='Expected surviving offspring',title='b  What is estimated')
    axes[1].legend(frameon=False,fontsize=8)
    return fig

def components_plot(settings,fitted,boot=None):
    true=truth(settings);est=fitted['estimate'];naive=fitted['naive']
    fig,axes=plt.subplots(1,2,figsize=(10,3.6),layout='tight')
    xx=np.arange(3);labels=['Generating model','Latent-value fit','Naive prediction fit']
    axes[0].bar(xx,[x['V_lin'] for x in [true,est,naive]],color=BLUE,label='Linear contribution')
    axes[0].bar(xx,[x['V_quad'] for x in [true,est,naive]],bottom=[x['V_lin'] for x in [true,est,naive]],color=ORANGE,label='Quadratic contribution')
    axes[0].set(xticks=xx,xticklabels=labels,ylabel='Variance of log expected fitness',title='a  Report both variance components')
    axes[0].tick_params(axis='x',labelsize=8);axes[0].legend(frameon=False,fontsize=8)
    values=[x['A_g'] for x in [true,est,naive]]
    axes[1].scatter(values,xx,color=[GREY,BLUE,ORANGE],s=40,zorder=3)
    if boot and 'A_g' in boot['intervals']:
        lo,hi=boot['intervals']['A_g'];axes[1].plot([lo,hi],[1,1],color=BLUE,lw=2)
    axes[1].set(yticks=xx,yticklabels=labels,xlim=(0,1),xlabel='First-order variance share',title='b  Ratio and conditional uncertainty')
    axes[1].invert_yaxis();axes[1].grid(axis='x',alpha=.15)
    return fig

def diagnostics_plot(fitted):
    """Bin on observed measurements; never compare W bins to W_A at EBVs."""
    cal=fitted['calibration'];x=cal['averages'];idx=np.argsort(x)
    groups=np.array_split(idx,10)
    p=conditional_prediction(cal,fitted['fit']);q=conditional_prediction(cal,fitted['alternative'])
    xm=[np.mean(x[g]) for g in groups]
    fig,axes=plt.subplots(1,2,figsize=(10,3.6),layout='tight')
    observed=[cal['W'][g].mean() for g in groups]
    error=[1.96*np.sqrt(np.sum(p[1][g]))/len(g) for g in groups]
    axes[0].errorbar(xm,observed,yerr=error,fmt='o',ms=4,color=GREY,label='Observed mean; model sampling bars')
    axes[0].plot(xm,[p[0][g].mean() for g in groups],color=BLUE,label='Quadratic fit')
    axes[0].plot(xm,[q[0][g].mean() for g in groups],color=ORANGE,ls='--',label='Quartic sensitivity fit')
    axes[0].set(xlabel='Mean observed height deviation (cm)',ylabel='Mean offspring count',title='a  Check the mean relationship')
    axes[0].legend(frameon=False,fontsize=8)
    axes[1].plot(xm,[np.mean(cal['W'][g]==0) for g in groups],'o',color=GREY,label='Observed zero fraction')
    axes[1].plot(xm,[p[2][g].mean() for g in groups],color=BLUE,label='Quadratic prediction')
    axes[1].set(xlabel='Mean observed height deviation (cm)',ylabel='Fraction with zero offspring',ylim=(0,1),title='b  Check the observation model')
    axes[1].legend(frameon=False,fontsize=8)
    return fig
