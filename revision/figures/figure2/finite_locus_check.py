"""
Test the large-effect-loci interpretation of heavy-tailed BV departures.

Build breeding values from explicit finite-locus models:
  - 'infinitesimal': many small-effect loci (~Gaussian by CLT)
  - 'oligogenic':    one or two large-effect loci + small-effect loci
  - 'monogenic':     single large-effect locus + a bit of polygenic noise

Each model produces breeding values with the same marginal variance but
different distributional shapes. We then test:
  1. Does the oligogenic/monogenic case actually produce heavier tails?
  2. Does Ag still equal R^2 under these models? (it should — the identity is
     about the local geometry, not the BV distribution shape)
  3. Does linear-only selection outcome track the full outcome?
"""
import numpy as np
import pandas as pd
from sim_core import (analytical_Ag, empirical_R2, empirical_spearman,
                      selection_outcome, random_geometry_triple)


def sample_finite_locus(G_target, n_samples, rng, architecture='infinitesimal',
                        n_loci=200, n_traits=2):
    """
    Sample breeding values from a finite-locus additive model with a target
    covariance G_target. Different architectures produce different distributional
    shapes but matched covariance.
    
    architecture:
      'infinitesimal' — n_loci small-effect loci, effects per trait drawn from N(0, 1)
      'oligogenic'    — 2 large-effect loci (effect ~ 5x) + n_loci-2 small loci
      'monogenic'     — 1 large-effect locus (effect ~ 10x) + n_loci-1 small loci
    """
    n = G_target.shape[0]
    p = 0.5  # all loci at intermediate frequency
    
    # Build effect matrix B: (n_loci x n_traits) such that effect of locus l on trait k is B[l, k]
    if architecture == 'infinitesimal':
        B = rng.standard_normal((n_loci, n))
    elif architecture == 'oligogenic':
        B_small = rng.standard_normal((n_loci - 2, n))
        B_large = 5.0 * rng.standard_normal((2, n))
        B = np.vstack([B_large, B_small])
    elif architecture == 'monogenic':
        B_small = rng.standard_normal((n_loci - 1, n))
        B_large = 10.0 * rng.standard_normal((1, n))
        B = np.vstack([B_large, B_small])
    else:
        raise ValueError(architecture)
    
    # Sample diploid dosages (0, 1, 2) for each locus, n_samples individuals
    # Centred dosage has variance 2*p*(1-p) = 0.5
    # So var(BV_k) = sum_l 2 p (1-p) B[l,k]^2 = 0.5 * sum_l B[l,k]^2
    dosages = rng.binomial(2, p, size=(n_samples, n_loci))
    centred_dosages = dosages - 2 * p
    BV_raw = centred_dosages @ B  # (n_samples, n)
    
    # Rescale so empirical covariance matches G_target
    cov_raw = np.cov(BV_raw.T)
    # Whiten to identity, then colour to G_target
    L_raw = np.linalg.cholesky(cov_raw + 1e-10 * np.eye(n))
    BV_white = BV_raw @ np.linalg.inv(L_raw).T
    L_target = np.linalg.cholesky(G_target + 1e-10 * np.eye(n))
    BV_scaled = BV_white @ L_target.T
    return BV_scaled


def run_finite_locus_sweep(n_triples_per_arch=80, N_samples=20_000, seed=42):
    rng = np.random.default_rng(seed)
    rows = []
    
    architectures = ['infinitesimal', 'oligogenic', 'monogenic']
    G_scales = np.geomspace(0.1, 3.0, 8)
    n = 4
    
    triple_id = 0
    for G_scale in G_scales:
        replicates = max(1, n_triples_per_arch // len(G_scales))
        for _ in range(replicates):
            b, H, G = random_geometry_triple(n, rng, b_scale=1.0, H_scale=1.0,
                                             G_scale=float(G_scale), H_signature='negative')
            Ag, Vlin, Vquad = analytical_Ag(b, H, G)
            
            for arch in architectures:
                samples = sample_finite_locus(G, N_samples, rng, architecture=arch, n_loci=200)
                R2 = empirical_R2(samples, b, H)
                rho_s = empirical_spearman(samples, b, H)
                ms_lin, _ = selection_outcome(samples, b, H, 'linear')
                ms_full, _ = selection_outcome(samples, b, H, 'full')
                norm_full = np.linalg.norm(ms_full) + np.sqrt(np.trace(G))
                ms_diff = np.linalg.norm(ms_full - ms_lin) / max(norm_full, 1e-12)
                
                # Empirical excess kurtosis (averaged across dimensions)
                from scipy.stats import kurtosis
                kurt = float(np.mean([kurtosis(samples[:, k]) for k in range(n)]))
                
                rows.append({
                    'triple_id': triple_id,
                    'G_scale': G_scale,
                    'architecture': arch,
                    'Ag': Ag,
                    'R2': R2,
                    'spearman': rho_s,
                    'ms_diff': ms_diff,
                    'excess_kurtosis': kurt,
                })
            triple_id += 1
    return pd.DataFrame(rows)


if __name__ == "__main__":
    print("Running finite-locus sweep...")
    df = run_finite_locus_sweep(n_triples_per_arch=80, N_samples=20_000)
    df.to_csv('/home/claude/figs/output/finite_locus_sweep.csv', index=False)
    
    print(f"\nTotal rows: {len(df)}")
    
    print("\n=== Empirical excess kurtosis by architecture ===")
    print(df.groupby('architecture')['excess_kurtosis'].describe()[['mean', 'std', 'min', 'max']].round(3))
    
    print("\n=== |Ag - R^2| by architecture ===")
    df['abs_diff'] = (df['Ag'] - df['R2']).abs()
    print(df.groupby('architecture')['abs_diff'].describe()[['mean', '50%', '75%', 'max']].round(4))
    
    print("\n=== ms_diff at high Ag (>0.75), by architecture ===")
    high = df[df['Ag'] > 0.75]
    print(high.groupby('architecture')['ms_diff'].describe()[['count', 'mean', '50%', 'max']].round(4))
    
    print("\n=== ms_diff at low Ag (<0.25), by architecture ===")
    low = df[df['Ag'] < 0.25]
    print(low.groupby('architecture')['ms_diff'].describe()[['count', 'mean', '50%', 'max']].round(4))
