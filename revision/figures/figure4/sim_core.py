"""
sim_core.py — minimal inheritance dynamics for the additive-channels framework

Implements the manuscript's per-generation update for the additive genetic
covariance G under Gaussian fitness and the Bulmer-style inheritance recursion
(Eqs. "bulmer-genic" and "bulmer-LD" in paper_1).

Notation
--------
n      number of trait dimensions
G      n x n PSD additive genetic covariance
G_genic  n x n PSD genic component (depends only on allele frequencies)
b      n vector — directional component of the local log-fitness gradient
                 (held externally constant in this script: "sustained selection")
Gamma  n x n PSD curvature of -log W, i.e. H = -Gamma
E      n x n PSD environmental phenotypic covariance
M      n x n PSD mutational input per generation
rho    scalar in [0,1] — LD retention per generation (1 = clonal, 0 = full recomb)

Per-generation update (matches manuscript Eqs. bulmer-genic, bulmer-LD)
----------------------------------------------------------------------
1.  V       = G + E                                     (phenotypic covariance)
2.  V_sel   = (V^-1 + Gamma)^-1                         (post-selection V; Gaussian)
3.  G_sel   = G - G V^-1 (V - V_sel) V^-1 G              (post-selection G)
4.  G_genic'  = G_genic + M                              (mutation adds genic var)
5.  G_{t+1}   = G_genic' + rho * (G_sel - G_genic')      (LD attenuated by 1-rho)

Sanity:
- When E = 0, G_sel reduces to (G^-1 + Gamma)^-1 (verified in tests below).
- When rho = 0, G_{t+1} = G_genic' (recombination fully resets LD each generation).
- When rho = 1, G_{t+1} = G_sel (fully clonal: selection-induced LD is preserved).

Additivity index
----------------
A_g  = V_lin / (V_lin + V_quad)
V_lin  = b^T G b              (sensitivity along b)
V_quad = 0.5 tr[(H G)^2] = 0.5 tr[(Gamma G)^2]   (since H = -Gamma)
"""

import numpy as np


# -------- numerical helpers --------------------------------------------------

def sym(A):
    """Symmetrise a matrix (kills numerical asymmetry from FP arithmetic)."""
    return 0.5 * (A + A.T)


def psd_inv(A, jitter=1e-12):
    """Symmetric positive-semidefinite inverse with small jitter for stability."""
    n = A.shape[0]
    return np.linalg.inv(sym(A) + jitter * np.eye(n))


# -------- additivity index ---------------------------------------------------

def additivity_index(G, b, Gamma):
    """Return (A_g, V_lin, V_quad) at the population mean.

    A_g = V_lin / (V_lin + V_quad)
    V_lin  = b' G b
    V_quad = 1/2 tr[(Gamma G)^2]   (since H = -Gamma)
    """
    GG  = G @ Gamma  # n x n
    Vq  = 0.5 * np.trace(GG @ GG)
    Vl  = float(b @ G @ b)
    return Vl / (Vl + Vq), Vl, Vq


# -------- per-generation update ---------------------------------------------

def step(G, G_genic, b, Gamma, E, M, rho, Ne=None):
    """
    One generation of the inheritance recursion. Returns (G_new, G_genic_new).

    G_sel is computed by Pearson selection on the phenotype with Gaussian
    fitness, then projected onto breeding values via the standard
    quantitative-genetics regression a | z = G V^-1 z.

    Optional Ne (effective population size) adds a Lynch-Hill mutation-drift
    closure on the genic component:    G_genic_new = G_genic + M - G_genic/Ne
    so that G_genic equilibrates at G_genic^* = Ne * M (textbook M-S-D balance).
    Set Ne=None for the manuscript's bare recursion (short-term only).
    """
    V    = sym(G + E)
    Vinv = psd_inv(V)
    Vsel = psd_inv(Vinv + Gamma)               # post-selection phenotypic cov

    # Drop in V from selection acts only through the breeding-value channel:
    GV   = G @ Vinv
    G_sel = sym(G - GV @ (V - Vsel) @ GV.T)

    # Genic update: mutation in, drift out (Lynch-Hill 1986; Walsh-Lynch ch. 12).
    if Ne is None:
        G_genic_new = sym(G_genic + M)
    else:
        G_genic_new = sym(G_genic + M - G_genic / Ne)

    # LD update: selection-induced LD attenuated by 1-rho each generation.
    G_new = sym(G_genic_new + rho * (G_sel - G_genic_new))
    return G_new, G_genic_new


def _b_at(b, t):
    """Resolve b at time t. Accepts a vector (constant b) or a callable b(t)."""
    return b(t) if callable(b) else b


def trajectory(G0, G_genic0, b, Gamma, E, M, rho, n_gen, Ne=None):
    """Run the recursion for n_gen generations. Returns dict of trajectories.

    Parameters
    ----------
    b : array (n,) OR callable t -> array (n,)
        If an array, b is held constant (sustained selection). If a callable,
        b(t) is queried each generation, allowing episodic / time-varying
        directional pressure (e.g. for natural populations with bouts of
        directional selection separated by mutation-drift balance).

    All other args as in step().
    """
    n = G0.shape[0]
    G = G0.copy()
    Gg = G_genic0.copy()

    out = {
        'G':       np.zeros((n_gen + 1, n, n)),
        'G_genic': np.zeros((n_gen + 1, n, n)),
        'tr_G':    np.zeros(n_gen + 1),
        'A_g':     np.zeros(n_gen + 1),
        'V_lin':   np.zeros(n_gen + 1),
        'V_quad':  np.zeros(n_gen + 1),
        'b_norm':  np.zeros(n_gen + 1),  # ||b(t)|| — useful for plotting episodes
    }
    out['G'][0] = G;  out['G_genic'][0] = Gg
    bt = _b_at(b, 0)
    Ag, Vl, Vq = additivity_index(G, bt, Gamma)
    out['tr_G'][0] = np.trace(G);  out['A_g'][0] = Ag
    out['V_lin'][0] = Vl;          out['V_quad'][0] = Vq
    out['b_norm'][0] = float(np.linalg.norm(bt))

    for t in range(1, n_gen + 1):
        bt = _b_at(b, t)
        G, Gg = step(G, Gg, bt, Gamma, E, M, rho, Ne=Ne)
        Ag, Vl, Vq = additivity_index(G, bt, Gamma)
        out['G'][t] = G;  out['G_genic'][t] = Gg
        out['tr_G'][t] = np.trace(G);  out['A_g'][t] = Ag
        out['V_lin'][t] = Vl;          out['V_quad'][t] = Vq
        out['b_norm'][t] = float(np.linalg.norm(bt))

    return out


# -------- self-tests ---------------------------------------------------------

def _self_test():
    """Three independent checks of the recursion before any figure is built."""
    rng = np.random.default_rng(0)
    n = 4

    # Random PSD test matrices
    A = rng.standard_normal((n, n));  G = sym(A @ A.T) + 0.5 * np.eye(n)
    A = rng.standard_normal((n, n));  Gamma = sym(A @ A.T) * 0.05 + 0.05 * np.eye(n)
    E = 0.1 * np.eye(n)
    b = rng.standard_normal(n) * 0.3

    # 1) E = 0 should reduce G_sel to (G^-1 + Gamma)^-1
    G_sel_full   = step(G, G, b, Gamma, np.zeros((n, n)), np.zeros((n, n)), rho=1.0)[0]
    G_sel_simple = psd_inv(psd_inv(G) + Gamma)
    err1 = np.max(np.abs(G_sel_full - G_sel_simple))
    assert err1 < 1e-9, f'E=0 reduction failed: max abs err {err1:.2e}'

    # 2) rho = 0 should give G_{t+1} = G_genic + M
    M = 0.01 * np.eye(n)
    G_next, _ = step(G, G, b, Gamma, E, M, rho=0.0)
    G_expected = G + M
    err2 = np.max(np.abs(G_next - G_expected))
    assert err2 < 1e-12, f'rho=0 update failed: max abs err {err2:.2e}'

    # 3) Selection always shrinks variance: tr(G_sel) <= tr(G) for any psd Gamma
    G_sel = step(G, G, b, Gamma, E, np.zeros((n, n)), rho=1.0)[0]
    assert np.trace(G_sel) <= np.trace(G) + 1e-9, 'selection failed to compress variance'

    # 4) A_g is in (0, 1] for nonzero b and psd G, Gamma
    Ag, Vl, Vq = additivity_index(G, b, Gamma)
    assert 0 < Ag <= 1, f'A_g out of bounds: {Ag}'

    print('sim_core self-test passed.')
    print(f'  E=0 reduction max abs err:           {err1:.2e}')
    print(f'  rho=0 update max abs err:            {err2:.2e}')
    print(f'  tr(G_sel) - tr(G) = {np.trace(G_sel) - np.trace(G):.4f} (should be <= 0)')
    print(f'  random A_g sanity:                   {Ag:.4f}')


if __name__ == '__main__':
    _self_test()
