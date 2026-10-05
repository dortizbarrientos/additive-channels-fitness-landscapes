"""Scientific checks, runnable with Python's standard-library unittest."""
import unittest
import numpy as np
from scipy.integrate import quad
from scipy.stats import norm,poisson
from model import (Settings,simulate,analyse,bootstrap,components,quadrature,
                   fit_surface,conditional_prediction,calibrate,truth)

class EstimationChecks(unittest.TestCase):
    def test_gaussian_moments_and_boundary(self):
        x,w=quadrature(41)
        np.testing.assert_allclose([w.sum(),x@w,(x*x)@w,(x**4)@w],[1,0,1,3],atol=1e-12)
        self.assertAlmostEqual(components(.7,-.7,1)['A_g'],2/3)
        self.assertEqual(components(1,0,1)['A_g'],1)
        self.assertEqual(components(0,-1,1)['A_g'],0)
        self.assertTrue(np.isnan(components(0,0,1)['A_g']))

    def test_simulation_reproducibility_and_hidden_truth(self):
        d,A=simulate();d2,A2=simulate()
        np.testing.assert_array_equal(d,d2);np.testing.assert_array_equal(A,A2)
        self.assertNotIn('A',d.columns)
        self.assertTrue((d.offspring==0).any())
        f=analyse(d,sensitivity=False)
        # Shuffling the truth file cannot change the estimator: it is never supplied.
        np.random.default_rng(4).shuffle(A)
        g=analyse(d,sensitivity=False)
        self.assertEqual(f['estimate'],g['estimate'])

    def test_integration_against_closed_mean_and_adaptive_integral(self):
        d,_=simulate();f=analyse(d,sensitivity=False);c=f['calibration'];t=f['fit']['theta']
        M=c['posterior_mean'][:5];v=c['posterior_var']
        predicted=conditional_prediction(c,f['fit'],M)[0]
        exact=np.exp(t[0]+t[1]*M+.5*t[2]*M*M+.5*v*(t[1]+t[2]*M)**2/(1-t[2]*v))/np.sqrt(1-t[2]*v)
        np.testing.assert_allclose(predicted,exact,rtol=1e-10)
        nodes,w=quadrature(81);m=M[0];count=c['W'][0]
        z=m+np.sqrt(v)*nodes
        likelihood=poisson.pmf(count,np.exp(t[0]+t[1]*z+.5*t[2]*z*z))@w
        independent=quad(lambda z:poisson.pmf(count,np.exp(t[0]+t[1]*z+.5*t[2]*z*z))*norm.pdf(z,m,np.sqrt(v)),m-12*np.sqrt(v),m+12*np.sqrt(v),epsabs=1e-12)[0]
        self.assertAlmostEqual(likelihood,independent,places=10)

    def test_known_value_limit_and_recovery(self):
        s=Settings(n=5000,seed=20261009,E=.1);d,A=simulate(s)
        fitted=fit_surface(A,0,d.offspring.to_numpy())
        self.assertLess(abs(fitted['theta'][1]-s.b),.06)
        self.assertLess(abs(fitted['theta'][2]-s.H),.08)
        estimates=[]
        for seed in range(42,62):
            d,_=simulate(Settings(seed=seed));estimates.append(analyse(d,sensitivity=False)['estimate']['A_g'])
        self.assertLess(abs(np.mean(estimates)-2/3),.05)

    def test_bootstrap_refits_measurement_variance(self):
        d,_=simulate();f=analyse(d,sensitivity=False)
        b=bootstrap(d,f,repeats=30,seed=81)
        self.assertEqual(len(b['failed']),0)
        self.assertGreater(b['draws']['G'].std(),0)
        self.assertGreater(b['draws']['E'].std(),0)
        self.assertTrue(0<=b['intervals']['A_g'][0]<b['intervals']['A_g'][1]<=1)

    def test_quartic_truth_is_not_quadratic_share(self):
        s=Settings(quartic=.08)
        t=truth(s);self.assertAlmostEqual(t['A_g'],2/3)
        x,w=quadrature(81);x=x*np.sqrt(s.G)
        ell=s.b*x+.5*s.H*x*x-s.quartic*x**4
        var=((ell-ell@w)**2)@w
        self.assertAlmostEqual(t['full_log_mean_R2'],s.b*s.b*s.G/var)
        self.assertLess(t['full_log_mean_R2'],.25)

    def test_sensitive_integration_and_quartic_fit(self):
        d,_=simulate();f=analyse(d)
        self.assertLess(f['alternative']['theta'][-1],0)
        self.assertGreaterEqual(f['alternative']['loglik'],f['fit']['loglik']-1e-5)
        self.assertGreater(f['fit']['checked_order'],f['fit']['order'])
        extreme=Settings(n=300,G=3,E=4,repeats=2,b=1.5,H=-.1,mean_output=10)
        d,_=simulate(extreme)
        with self.assertRaisesRegex(ValueError,'integration did not stabilise'):
            analyse(d,sensitivity=False)

    def test_failed_calibration_is_not_truncated(self):
        d,_=simulate();cols=[c for c in d if c.startswith('height_')]
        d[cols]=0
        with self.assertRaises(ValueError):calibrate(d)

if __name__=='__main__':unittest.main()
