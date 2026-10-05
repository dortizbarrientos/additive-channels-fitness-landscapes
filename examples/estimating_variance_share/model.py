"""A one-trait, measurement-error example for Supplementary File 3.

Only the simulator sees true breeding values. The estimator accepts repeated
trait measurements and integer reproductive counts. It first estimates the
measurement model, then integrates over uncertain breeding values when fitting
fitness. This is a two-stage estimator, not a joint animal-model analysis.
"""
from dataclasses import dataclass, asdict
from functools import lru_cache
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import roots_hermitenorm, logsumexp, gammaln

@dataclass(frozen=True)
class Settings:
    n: int = 800
    repeats: int = 3
    G: float = 1.0
    E: float = 1.0
    b: float = 0.7
    H: float = -0.7
    mean_output: float = 4.0  # W_A at the population mean, not population mean W.
    quartic: float = 0.0     # Adds -quartic*A**4; the primary fit stays quadratic.
    seed: int = 20261005

    def validate(self):
        values=[self.G,self.E,self.b,self.H,self.mean_output,self.quartic]
        if not all(np.isfinite(values)):
            raise ValueError('Parameters must be finite.')
        if not (100 <= self.n <= 5000 and 2 <= self.repeats <= 10):
            raise ValueError('Use 100–5000 genotypes and 2–10 measurements.')
        if not (0.1 <= self.G <= 3 and 0.01 <= self.E <= 4):
            raise ValueError('Use G in [0.1, 3] and environmental variance in [0.01, 4].')
        if not (-1.5 <= self.b <= 1.5 and -2 <= self.H <= -0.05):
            raise ValueError('Use a slope in [-1.5, 1.5] and negative curvature in [-2, -0.05].')
        if not (0.5 <= self.mean_output <= 10 and 0 <= self.quartic <= 0.2):
            raise ValueError('Expected output must be 0.5–10 and quartic strength 0–0.2.')
        if not (0 <= self.seed < 2**32):
            raise ValueError('Seed must be a nonnegative 32-bit integer.')


def components(b, H, G):
    """Variance in a quadratic log conditional mean, not variance of counts."""
    linear=float(b*b*G)
    quadratic=float(0.5*H*H*G*G)
    return dict(b=float(b), H=float(H), G=float(G), V_lin=linear,
                V_quad=quadratic, A_g=linear/(linear+quadratic) if linear+quadratic>0 else np.nan)


def simulate(settings=Settings()):
    """Separate observable data from truth so no fitted model can use A by accident.

    Trait measurements are independent clonal replicates under an explicitly
    additive trait model. Dominance, epistasis, permanent environment and a
    shared environment with the reproductive assay are absent by construction.
    """
    settings.validate()
    rng=np.random.default_rng(settings.seed)
    A=rng.normal(0,np.sqrt(settings.G),settings.n)
    Y=A[:,None]+rng.normal(0,np.sqrt(settings.E),(settings.n,settings.repeats))
    log_mean=np.log(settings.mean_output)+settings.b*A+0.5*settings.H*A*A-settings.quartic*A**4
    W=rng.poisson(np.exp(log_mean))
    return pd.DataFrame({'id':np.arange(1,settings.n+1),'offspring':W,
                         **{f'height_{j+1}':Y[:,j] for j in range(settings.repeats)}}), A


def calibrate(data):
    """Balanced repeated-measurement ANOVA estimates of within and genetic variance.

    Var(mean height) = G + E/m. Subtract the estimated environmental contribution.
    Nonpositive genetic variance is a failed calibration, not silently truncated.
    """
    columns=[c for c in data if c.startswith('height_')]
    Y=data[columns].to_numpy(float)
    W=data['offspring'].to_numpy(float)
    n,m=Y.shape
    if n<20 or m<2 or not np.isfinite(Y).all() or not np.isfinite(W).all():
        raise ValueError('Need finite measurements on at least 20 genotypes with at least two repeats.')
    if np.any(W<0) or np.any(W!=np.floor(W)) or W.sum()==0:
        raise ValueError('Reproductive counts must be nonnegative integers, with at least one positive count.')
    averages=Y.mean(axis=1);mu=averages.mean()
    E=np.sum((Y-averages[:,None])**2)/(n*(m-1))
    G=np.var(averages,ddof=1)-E/m
    if G<=1e-8:
        raise ValueError('The repeated measurements do not resolve positive breeding-value variance. Increase sample size or replication.')
    reliability=G/(G+E/m)
    return dict(n=n,repeats=m,mu=float(mu),G=float(G),E=float(E),
                reliability=float(reliability),posterior_mean=reliability*(averages-mu),
                posterior_var=float(G*(1-reliability)),averages=averages,W=W)

@lru_cache(maxsize=12)
def quadrature(order):
    """Normal-expectation nodes and weights; the weights sum to one."""
    nodes,weights=roots_hermitenorm(order)
    return nodes,weights/np.sqrt(2*np.pi)


def fit_surface(means, variance, counts, degree=2, order=41, initial_theta=None):
    """Maximise P(W | repeated heights), integrating over latent A.

    Predictors are centred at the calibrated population mean. Coefficient 2
    multiplies z**2/2, so it IS H (no later factor-of-two conversion). The
    quartic sensitivity model adds z**3 and z**4, allowing a displaced centre.
    The negative highest even coefficient gives finite population moments.
    """
    nodes,weights=quadrature(order)
    z=np.asarray(means)[:,None]+np.sqrt(variance)*nodes[None,:]
    if variance==0: z=np.asarray(means)[:,None];weights=np.array([1.0])
    powers=[np.ones_like(z),z,0.5*z*z]
    if degree==4:powers.extend([z**3,z**4])
    X=np.stack(powers,axis=-1)
    counts=np.asarray(counts)
    const=gammaln(counts+1)[:,None]
    def loss(theta):
        eta=np.einsum('nqk,k->nq',X,theta)
        # These guards prevent floating-point overflow outside sensible fits.
        # They are not used to clip or alter the fitted response function.
        if np.max(eta)>600 or not np.isfinite(eta).all():return 1e100,np.zeros(len(theta))
        rate=np.exp(eta)
        ll=counts[:,None]*eta-rate-const+np.log(weights)[None,:]
        marginal=logsumexp(ll,axis=1)
        posterior=np.exp(ll-marginal[:,None])
        score=np.einsum('nq,nq,nqk->k',posterior,counts[:,None]-rate,X)
        return -marginal.mean(),-score/len(counts)
    initial=[np.log(max(counts.mean(),0.1)),0.3,-0.3]
    bounds=[(-7,7),(-5,5),(-6,0)]
    if degree==4:
        initial += [0,-0.01]
        bounds=[(-7,7),(-5,5),(-6,3),(-2,2),(-1,-1e-8)]
    starts=[np.array(initial),np.array(initial)*np.array([1,-1,1]+([1,1] if degree==4 else []))]
    if degree==4:
        quadratic=fit_surface(means,variance,counts,degree=2,order=order)
        starts.append(np.r_[quadratic['theta'],0,0])
    if initial_theta is not None:starts.insert(0,np.asarray(initial_theta))
    fits=[minimize(loss,t,jac=True,method='L-BFGS-B',bounds=bounds,
                   options={'ftol':1e-11,'gtol':1e-6,'maxiter':500}) for t in starts]
    good=[f for f in fits if f.success and np.isfinite(f.fun) and f.fun<1e90]
    if not good:raise ValueError('Fitness model did not converge. Try more genotypes or another seed.')
    f=min(good,key=lambda f:f.fun)
    boundary=any(min(abs(x-lo),abs(x-hi))<1e-5 for x,(lo,hi) in zip(f.x,bounds))
    return dict(theta=f.x,loglik=float(-f.fun*len(counts)),boundary=boundary,order=order,degree=degree)


def checked_surface(means, variance, counts, degree=2, order=41):
    """Increase integration order until coefficients and likelihood stabilise.

    High counts and imprecise trait measurements can make the integral sharp.
    Do not display a seemingly precise estimate from an unresolved integral.
    """
    previous=fit_surface(means,variance,counts,degree,order)
    for higher_order in sorted({81,161,321,2*order-1}):
        if higher_order<=previous['order']:continue
        current=fit_surface(means,variance,counts,degree,higher_order,previous['theta'])
        change=np.max(np.abs(current['theta']-previous['theta'])/(1+np.abs(current['theta'])))
        if change<1e-4 and abs(current['loglik']-previous['loglik'])/len(counts)<1e-6:
            previous['checked_order']=higher_order
            return previous
        previous=current
    raise ValueError('Numerical integration did not stabilise. Reduce output, slope or measurement noise, or increase replication.')


def analyse(data, order=41, sensitivity=True):
    """No truth argument exists here: both calibration and fitting use observables."""
    cal=calibrate(data)
    fitted=checked_surface(cal['posterior_mean'],cal['posterior_var'],cal['W'],order=order)
    result=components(fitted['theta'][1],fitted['theta'][2],cal['G'])
    result.update(alpha=float(fitted['theta'][0]),mu=cal['mu'],E=cal['E'],
                  reliability=cal['reliability'],boundary=fitted['boundary'],loglik=fitted['loglik'])
    answer=dict(calibration=cal,fit=fitted,estimate=result)
    if sensitivity:
        # Deliberately naive: shrinkage predictions are fitted as if observed,
        # and their empirical variance is substituted for G. Its bias has no
        # universal direction when the slopes and curvature are re-estimated.
        naive=fit_surface(cal['posterior_mean'],0,cal['W'])
        answer['naive']=components(naive['theta'][1],naive['theta'][2],np.var(cal['posterior_mean'],ddof=1))
        alternative=checked_surface(cal['posterior_mean'],cal['posterior_var'],cal['W'],degree=4,order=order)
        answer['alternative']=alternative
        answer['alternative_share']=components(alternative['theta'][1],alternative['theta'][2],cal['G'])
        answer['delta_aic']=float((2*5-2*alternative['loglik'])-(2*3-2*fitted['loglik']))
    return answer


def conditional_prediction(calibration, fit, means=None):
    """Predict counts at observed measurement information, not at exact A."""
    means=calibration['posterior_mean'] if means is None else np.asarray(means)
    nodes,weights=quadrature(max(81,fit.get('checked_order',fit['order'])))
    z=means[:,None]+np.sqrt(calibration['posterior_var'])*nodes[None,:]
    t=fit['theta'];eta=t[0]+t[1]*z+0.5*t[2]*z*z
    if len(t)==5:eta+=t[3]*z**3+t[4]*z**4
    rate=np.exp(eta)
    mean=rate@weights
    variance=mean+rate**2@weights-mean**2
    zero=np.exp(-rate)@weights
    return mean,variance,zero


def bootstrap(data, fitted, repeats=200, seed=20261006, progress=None):
    """Parametric bootstrap, resimulating trait replicates AND reproductive counts.

    Calibration and fitness fitting are repeated. This propagates their joint
    sampling uncertainty under the fitted quadratic measurement model. It does
    not cover model misspecification, relatedness or additional genetic terms.
    """
    if not 2<=repeats<=2000:raise ValueError('Use 2–2000 bootstrap replicates.')
    rng=np.random.default_rng(seed);cal=fitted['calibration'];e=fitted['estimate']
    n,m=cal['n'],cal['repeats'];rows=[];failures=[]
    for j in range(repeats):
        A=rng.normal(0,np.sqrt(e['G']),n)
        Y=e['mu']+A[:,None]+rng.normal(0,np.sqrt(e['E']),(n,m))
        W=rng.poisson(np.exp(e['alpha']+e['b']*A+0.5*e['H']*A*A))
        sample=pd.DataFrame({'offspring':W,**{f'height_{k+1}':Y[:,k] for k in range(m)}})
        try:
            b=analyse(sample,order=fitted['fit']['order'],sensitivity=False)['estimate']
            rows.append({'replicate':j+1,**b})
        except ValueError as error:failures.append({'replicate':j+1,'reason':str(error)})
        if progress:progress(j+1,repeats)
    draws=pd.DataFrame(rows)
    intervals={}
    if len(draws)>=max(2,int(.9*repeats)):
        for k in ['b','H','G','V_lin','V_quad','A_g']:
            intervals[k]=[float(x) for x in np.quantile(draws[k],[.025,.975])]
    return dict(draws=draws,intervals=intervals,failed=failures,requested=repeats,
                boundary_count=int(draws['boundary'].sum()) if len(draws) else 0,seed=seed)


def truth(settings):
    out=components(settings.b,settings.H,settings.G)
    # With a quartic term, this is the affine R² of the complete log mean.
    # It differs from the share in the local quadratic approximation.
    even_variance=out['V_quad']-12*settings.H*settings.quartic*settings.G**3+96*settings.quartic**2*settings.G**4
    out['full_log_mean_R2']=out['V_lin']/(out['V_lin']+even_variance)
    return out
