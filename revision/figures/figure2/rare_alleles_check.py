"""
Test the rare-large-effect-allele hypothesis:
  - 'common large-effect': large-effect locus at p = 0.5 (intermediate freq)
  - 'rare large-effect':   large-effect locus at p = 0.02 (rare)
  - 'rare large-effect, very rare': p = 0.005

Question: does rare-allele large-effect architecture produce heavy tails AND
break the operational additive-prediction claim?
"""
import numpy as np
import pandas as pd
from scipy.stats import kurtosis
from sim_core import (analytical_Ag, empirical_R2, selection_outcome,
                      random_geometry_triple)


def sample_with_rare_large_effect(G_target, n_samples, rng, p_rare=0.02, large_effect_size=10.0,
                                  n_small_loci=200):
    """
    1 large-effect locus at frequency p_rare with effect size = large_effect_size,
    plus many small-effect loci at p = 0.5 to make up the polygenic baseline.
    Then rescale so total covariance matches G_target.
    """
    n = G_target.shape[0]
    # Small-effect loci at common frequency
    small_dosages = rng.binomial(2, 0.5, size=(n_samples, n_small_loci))
    small_centred = small_dosages - 1.0
    B_small = rng.standard_normal((n_small_loci, n))
    BV_small = small_centred @ B_small
    
    # Large-effect locus at rare frequency
    rare_dosage = rng.binomial(2, p_rare, size=n_samples)
    rare_centred = rare_dosage - 2 * p_rare  # mean-centred
    b_large = large_effect_size * rng.standard_normal(n)
    BV_large = rare_centred[:, None] * b_large[None, :]
    
    BV_raw = BV_small + BV_large
    
    # Rescale to match G_target (whitening + colouring)
    cov_raw = np.cov(BV_raw.T)
    L_raw = np.linalg.cholesky(cov_raw + 1e-10 * np.eye(n))
    BV_white = BV_raw @ np.linalg.inv(L_raw).T
    L_target = np.linalg.cholesky(G_target + 1e-10 * np.eye(n))
    BV_scaled = BV_white @ L_target.T
    return BV_scaled


def run_rare_allele_sweep(n_triples=80, N_samples=20_000, seed=42):
    rng = np.random.default_rng(seed)
    rows = []
    
    architectures = [
        ('common (p=0.5)', 0.5, 5.0),
        ('rare (p=0.05)', 0.05, 10.0),
        ('rare (p=0.02)', 0.02, 10.0),
        ('very rare (p=0.005)', 0.005, 15.0),
    ]
    G_scales = np.geomspace(0.1, 3.0, 8)
    n = 4
    
    triple_id = 0
    for G_scale in G_scales:
        replicates = max(1, n_triples // len(G_scales))
        for _ in range(replicates):
            b, H, G = random_geometry_triple(n, rng, b_scale=1.0, H_scale=1.0,
                                             G_scale=float(G_scale), H_signature='negative')
            Ag, _, _ = analytical_Ag(b, H, G)
            
            for arch_label, p_rare, eff_size in architectures:
                samples = sample_with_rare_large_effect(G, N_samples, rng,
                                                       p_rare=p_rare,
                                                       large_effect_size=eff_size)
                R2 = empirical_R2(samples, b, H)
                ms_lin, _ = selection_outcome(samples, b, H, 'linear')
                ms_full, _ = selection_outcome(samples, b, H, 'full')
                norm_full = np.linalg.norm(ms_full) + np.sqrt(np.trace(G))
                ms_diff = np.linalg.norm(ms_full - ms_lin) / max(norm_full, 1e-12)
                kurt = float(np.mean([kurtosis(samples[:, k]) for k in range(n)]))
                
                rows.append({
                    'triple_id': triple_id,
                    'architecture': arch_label,
                    'p_rare': p_rare,
                    'Ag': Ag,
                    'R2': R2,
                    'ms_diff': ms_diff,
                    'excess_kurtosis': kurt,
                })
            triple_id += 1
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = run_rare_allele_sweep()
    df.to_csv('/home/claude/figs/output/rare_alleles_sweep.csv', index=False)
    
    print("=== Empirical excess kurtosis by architecture ===")
    print(df.groupby('architecture')['excess_kurtosis'].agg(['mean', 'std', 'max']).round(3))
    
    df['abs_diff'] = (df['Ag'] - df['R2']).abs()
    print("\n=== |Ag - R^2| by architecture ===")
    print(df.groupby('architecture')['abs_diff'].agg(['mean', 'median', 'max']).round(4))
    
    print("\n=== ms_diff at high Ag (>0.75) by architecture ===")
    high = df[df['Ag'] > 0.75]
    print(high.groupby('architecture')['ms_diff'].agg(['count', 'mean', 'median', 'max']).round(4))
    
    print("\n=== ms_diff at low Ag (<0.25) by architecture ===")
    low = df[df['Ag'] < 0.25]
    print(low.groupby('architecture')['ms_diff'].agg(['count', 'mean', 'median', 'max']).round(4))
