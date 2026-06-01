"""
Wide parameter sweep for Figure 2 v2 — using genetically realistic departures
from Gaussian (rare large-effect alleles) instead of multivariate t_4.

Three sample sources for each (b, H, G) triple:
  - Gaussian (canonical baseline)
  - Polygenic finite-locus (200 small-effect loci at p=0.5; CLT gives ~Gaussian)
  - Rare-large-effect (1 large-effect locus at p=0.02 + 200 small-effect loci)

Each tests a different claim:
  - Gaussian: identity holds exactly
  - Polygenic: identity holds because BV distribution is ~Gaussian by CLT
  - Rare-large-effect: identity holds approximately even under positive kurtosis
"""
import numpy as np
import pandas as pd
from scipy.stats import kurtosis
from sim_core import (analytical_Ag, empirical_R2, empirical_spearman,
                      selection_outcome, sample_gaussian, random_geometry_triple)

# Reuse the rare-large-effect sampler
import sys
from rare_alleles_check import sample_with_rare_large_effect


def sample_polygenic(G_target, n_samples, rng, n_loci=200):
    """200 small-effect loci, all at p=0.5; CLT gives Gaussian to high accuracy."""
    n = G_target.shape[0]
    dosages = rng.binomial(2, 0.5, size=(n_samples, n_loci))
    centred = dosages - 1.0
    B = rng.standard_normal((n_loci, n))
    BV_raw = centred @ B
    cov_raw = np.cov(BV_raw.T)
    L_raw = np.linalg.cholesky(cov_raw + 1e-10 * np.eye(n))
    BV_white = BV_raw @ np.linalg.inv(L_raw).T
    L_target = np.linalg.cholesky(G_target + 1e-10 * np.eye(n))
    return BV_white @ L_target.T


def run_sweep(n_triples=400, N_samples=20_000, seed=42):
    rng = np.random.default_rng(seed)
    rows = []

    dimensions = [2, 4, 8]
    G_scales = np.geomspace(0.05, 5.0, 12)
    H_signatures = ['negative', 'mixed']
    distributions = ['gaussian', 'polygenic', 'rare_large']

    triple_id = 0
    for n in dimensions:
        for G_scale in G_scales:
            for H_sig in H_signatures:
                replicates = max(1, n_triples // (len(dimensions) * len(G_scales) * len(H_signatures)))
                for replicate in range(replicates):
                    b, H, G = random_geometry_triple(
                        n, rng, b_scale=1.0, H_scale=1.0,
                        G_scale=float(G_scale), H_signature=H_sig,
                    )
                    Ag, Vlin, Vquad = analytical_Ag(b, H, G)

                    for dist in distributions:
                        if dist == 'gaussian':
                            samples = sample_gaussian(G, N_samples, rng)
                        elif dist == 'polygenic':
                            samples = sample_polygenic(G, N_samples, rng, n_loci=200)
                        elif dist == 'rare_large':
                            samples = sample_with_rare_large_effect(
                                G, N_samples, rng, p_rare=0.02,
                                large_effect_size=10.0, n_small_loci=200)
                        R2 = empirical_R2(samples, b, H)
                        rho_s = empirical_spearman(samples, b, H)
                        kurt = float(np.mean([kurtosis(samples[:, k]) for k in range(n)]))
                        ms_lin, pc_lin = selection_outcome(samples, b, H, 'linear')
                        ms_full, pc_full = selection_outcome(samples, b, H, 'full')
                        norm_full = np.linalg.norm(ms_full) + np.sqrt(np.trace(G))
                        ms_diff = np.linalg.norm(ms_full - ms_lin) / max(norm_full, 1e-12)

                        rows.append({
                            'triple_id': triple_id, 'n': n, 'G_scale': G_scale,
                            'H_sig': H_sig, 'dist': dist, 'Ag': Ag,
                            'Vlin': Vlin, 'Vquad': Vquad, 'R2': R2,
                            'spearman': rho_s, 'ms_diff': ms_diff,
                            'excess_kurtosis': kurt,
                        })
                    triple_id += 1
    return pd.DataFrame(rows)


if __name__ == "__main__":
    print("Running sweep with biologically realistic departures...")
    df = run_sweep(n_triples=400, N_samples=20_000, seed=42)
    df.to_csv('validation_sweep.csv', index=False)
    print(f"Total rows: {len(df)}")
    print(f"Triples: {df['triple_id'].nunique()}")

    print("\n=== Excess kurtosis by distribution ===")
    print(df.groupby('dist')['excess_kurtosis'].agg(['mean', 'std', 'max']).round(3))

    print("\n=== |Ag - R^2| by distribution ===")
    df['abs_diff'] = (df['Ag'] - df['R2']).abs()
    print(df.groupby('dist')['abs_diff'].agg(['median', 'mean', 'max']).round(4))

    print("\n=== ms_diff at high Ag (>0.75) by distribution ===")
    high = df[df['Ag'] > 0.75]
    print(high.groupby('dist')['ms_diff'].agg(['count', 'median', 'mean', 'max']).round(4))

    print("\n=== ms_diff at low Ag (<0.25) by distribution ===")
    low = df[df['Ag'] < 0.25]
    print(low.groupby('dist')['ms_diff'].agg(['count', 'median', 'mean', 'max']).round(4))
