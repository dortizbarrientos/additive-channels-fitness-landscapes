"""
Adaptation simulation v2: maintained directional selection with eventual relaxation.

Scenario: a population experiences a directional gradient b(t) that decays over 
time (representing, e.g., environmental change subsiding, or the breeder relaxing 
selection). σ² compresses under stabilising curvature γ. As long as |b| remains 
substantial, V_lin = |b|²σ² stays substantial while V_quad = (1/2) n γ² σ⁴ shrinks 
faster (σ⁴ decreases faster than σ²). A_g rises.

When |b| eventually decays toward zero, V_lin → 0 and A_g → 0. This gives the 
rise-then-fall dynamic the manuscript describes.

Alternatively: 'maintained directional selection' under a moving optimum, where 
b is approximately constant for a sustained period before relaxing.

We simulate the cleanest version: b decays exponentially with rate λ_b, σ² 
follows its compression dynamics under stabilising curvature γ.
"""
import numpy as np
import pandas as pd

def simulate_directional_then_relaxed(n=4, gamma=0.05, b0=1.0, lambda_b=0.005,
                                       rho=0.95, M=1e-3, sigma2_0=10.0,
                                       n_gen=500, seed=42):
    """
    State: σ² and |b|. We don't track displacement separately because b is 
    exogenous (set by an external pressure that decays over time).
    
    Per generation:
      Selection compresses variance: σ²_sel = σ²/(1 + γσ²) (Level 1, isotropic)
      Inheritance: σ²_new = σ²_genic + ρ(σ²_sel - σ²_genic), σ²_genic += M
      Gradient: |b|(t) = b0 * exp(-λ_b * t)  (exponential decay)
      
    A_g = V_lin / (V_lin + V_quad) = |b|²σ² / (|b|²σ² + (1/2)nγ²σ⁴)
        = 1 / (1 + nγ²σ²/(2|b|²))
    """
    sigma2 = np.zeros(n_gen)
    b_mag = np.zeros(n_gen)
    Ag = np.zeros(n_gen)
    Vlin = np.zeros(n_gen)
    Vquad = np.zeros(n_gen)
    
    sigma2[0] = sigma2_0
    sigma2_genic = sigma2_0
    
    for t in range(n_gen):
        b_mag[t] = b0 * np.exp(-lambda_b * t)
        s2 = sigma2[t] if t > 0 else sigma2_0
        Vlin[t] = b_mag[t]**2 * s2
        Vquad[t] = 0.5 * n * gamma**2 * s2**2
        Ag[t] = Vlin[t] / (Vlin[t] + Vquad[t]) if (Vlin[t] + Vquad[t]) > 1e-15 else 0
        # Update for next gen
        if t < n_gen - 1:
            s2_sel = s2 / (1.0 + gamma * s2)
            sigma2_genic_new = sigma2_genic + M
            s2_new = sigma2_genic_new + rho * (s2_sel - sigma2_genic_new)
            sigma2[t+1] = s2_new
            sigma2_genic = sigma2_genic_new
    
    return pd.DataFrame({
        'generation': np.arange(n_gen),
        'sigma2': sigma2,
        'sigma': np.sqrt(sigma2),
        'b_mag': b_mag,
        'Vlin': Vlin,
        'Vquad': Vquad,
        'Ag': Ag,
    })


if __name__ == "__main__":
    df = simulate_directional_then_relaxed(
        n=4, gamma=0.05, b0=1.0, lambda_b=0.005, rho=0.95, M=1e-3,
        sigma2_0=10.0, n_gen=500
    )
    print("=== Trajectory summary ===")
    print(f"Initial: σ² = {df['sigma2'].iloc[0]:.3f}, |b| = {df['b_mag'].iloc[0]:.3f}, "
          f"A_g = {df['Ag'].iloc[0]:.3f}")
    
    peak = df['Ag'].idxmax()
    print(f"\nPeak A_g = {df['Ag'].iloc[peak]:.3f} at generation {peak}")
    print(f"  At peak: σ² = {df['sigma2'].iloc[peak]:.3f}, |b| = {df['b_mag'].iloc[peak]:.3f}")
    
    # In channel
    in_channel = df['Ag'] >= 0.75
    if in_channel.any():
        first = in_channel.idxmax()
        last = first
        for i in range(first, len(df)):
            if df['Ag'].iloc[i] >= 0.75:
                last = i
            else:
                break
        print(f"\nIn additive channel (A_g ≥ 0.75): generations {first}–{last} ({last-first+1} gens)")
    
    print(f"\nLate stage:")
    print(f"  At gen 200: σ² = {df['sigma2'].iloc[200]:.4f}, |b| = {df['b_mag'].iloc[200]:.4f}, A_g = {df['Ag'].iloc[200]:.4f}")
    print(f"  At gen 499: σ² = {df['sigma2'].iloc[499]:.4f}, |b| = {df['b_mag'].iloc[499]:.4f}, A_g = {df['Ag'].iloc[499]:.4f}")
    
    df.to_csv('/home/claude/figs/output/adaptation_v2.csv', index=False)
