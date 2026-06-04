"""
compute_diagnostics.py
======================

Reads the per-generation breeding-value (BV) dump produced by the SLiM
simulation and computes the additive-channels framework's diagnostics at
each generation.

GENERALISED to support:
  - ARBITRARY NUMBER OF TRAITS: auto-detected from the BV CSV columns
    (a1, a2, ..., aN).  Same code path handles n_traits = 2 (the simple
    PoC) or n_traits = 4 (the extended scenario), or any other size.
  - TIME-VARYING OPTIMUM: optionally read from a separate optimum CSV
    (one row per generation with columns z_opt_1, z_opt_2, ...).  If no
    optimum CSV is given, --z-opt-static is used as a constant.

PER-GENERATION OUTPUT COLUMNS
-----------------------------
  gen, N
  a_bar_k for k = 1..n_traits          (population mean BVs)
  z_opt_k for k = 1..n_traits          (optimum at this generation)
  G_kk    for k = 1..n_traits          (G diagonal, for inspection)
  eig_G_k for k = 1..n_traits          (eigenvalues of G, descending)
  mu_k    for k = 1..n_traits          (eigenvalues of -HG = Gamma G,
                                        descending positive)
  b_k     for k = 1..n_traits          (analytical gradient)
  b_norm                               (||b||)
  V_lin, V_quad, A_g, R2_empirical, Ag_minus_R2

USAGE
-----
  # Simple PoC (static optimum, command-line z*)
  python compute_diagnostics.py \
      --bv-input  output/rep_01_bv.csv \
      --output    output/diag_rep_01.csv \
      --gammas    0.10 0.05 \
      --z-opt-static -2.0 0.0

  # Extended scenario (moving optimum, z*(t) read from file)
  python compute_diagnostics.py \
      --bv-input   output/rep_4t_bv.csv \
      --opt-input  output/rep_4t_opt.csv \
      --output     output/diag_rep_4t.csv \
      --gammas     0.10 0.05 0.04 0.03
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
#  Auto-detection helpers
# ---------------------------------------------------------------------------

def detect_n_traits(df: pd.DataFrame) -> int:
    """
    Count columns matching 'aK' where K is a positive integer (a1, a2, ...).
    These are the per-trait BV columns written by the SLiM script.
    """
    trait_cols = [c for c in df.columns
                  if c.startswith("a") and c[1:].isdigit()]
    if not trait_cols:
        sys.exit("ERROR: no trait columns found (expected a1, a2, ...).")
    # Verify they are 1..N consecutively
    indices = sorted(int(c[1:]) for c in trait_cols)
    if indices != list(range(1, len(indices) + 1)):
        sys.exit(f"ERROR: trait columns are not consecutive 1..N "
                 f"(found {indices}).")
    return len(trait_cols)


# ---------------------------------------------------------------------------
#  Core computation
# ---------------------------------------------------------------------------

def compute_diagnostics_per_generation(
    df_bv: pd.DataFrame,
    df_opt: Optional[pd.DataFrame],
    gammas: np.ndarray,
    z_opt_static: Optional[np.ndarray] = None,
) -> pd.DataFrame:
    """
    Compute the framework's diagnostics at each generation.

    Parameters
    ----------
    df_bv : DataFrame
        Long-format BVs with columns ['generation', 'individual',
        'a1', 'a2', ..., 'aN'].
    df_opt : DataFrame or None
        Optional time-varying optimum, with columns ['generation',
        'z_opt_1', 'z_opt_2', ..., 'z_opt_N'].  If None, z_opt_static is
        used at every generation.
    gammas : array, shape (n_traits,)
        Diagonal entries of Gamma.
    z_opt_static : array or None
        Constant optimum, used when df_opt is None.
    """
    n_traits = detect_n_traits(df_bv)
    trait_cols = [f"a{k+1}" for k in range(n_traits)]

    if len(gammas) != n_traits:
        sys.exit(f"ERROR: --gammas has {len(gammas)} entries but data has "
                 f"{n_traits} traits.")

    Gamma = np.diag(gammas)
    H = -Gamma                  # log-fitness Hessian (constant)

    # Build a (gen -> z*) lookup
    if df_opt is not None:
        opt_cols = [f"z_opt_{k+1}" for k in range(n_traits)]
        missing = [c for c in opt_cols if c not in df_opt.columns]
        if missing:
            sys.exit(f"ERROR: optimum CSV is missing columns {missing}.")
        z_opt_by_gen = {
            int(row["generation"]): row[opt_cols].to_numpy(dtype=float)
            for _, row in df_opt.iterrows()
        }
    else:
        if z_opt_static is None:
            sys.exit("ERROR: must provide either --opt-input or --z-opt-static.")
        if len(z_opt_static) != n_traits:
            sys.exit(f"ERROR: --z-opt-static has {len(z_opt_static)} entries "
                     f"but data has {n_traits} traits.")
        z_opt_by_gen = None     # signal to use static below
        z_opt_static = np.asarray(z_opt_static, dtype=float)

    rows = []

    for gen, sub in df_bv.groupby("generation", sort=True):
        a = sub[trait_cols].to_numpy()              # (N, n_traits)
        N = a.shape[0]
        a_bar = a.mean(axis=0)                      # (n_traits,)
        delta_a = a - a_bar                         # (N, n_traits)

        # Determine z*(gen)
        if z_opt_by_gen is not None:
            if int(gen) not in z_opt_by_gen:
                sys.exit(f"ERROR: optimum CSV missing row for generation {gen}.")
            z_opt = z_opt_by_gen[int(gen)]
        else:
            z_opt = z_opt_static

        # ---- Empirical G ----
        G = np.cov(a, rowvar=False, ddof=1)
        # Edge case: with n_traits=1, np.cov returns a scalar.  Promote to 2D.
        G = np.atleast_2d(G)

        # ---- Eigenvalues of G ----
        eig_G = np.sort(np.linalg.eigvalsh(G))[::-1]    # descending

        # ---- Eigenvalues of -HG = Gamma G (the framework's mu_i) ----
        # Gamma G is similar to G^(1/2) Gamma G^(1/2) (symmetric pos-def),
        # so eigenvalues are real positive.
        neg_HG = Gamma @ G
        eig_neg_HG = np.real(np.linalg.eigvals(neg_HG))
        mu = np.sort(eig_neg_HG)[::-1]                  # descending positive

        # ---- Analytical b at population mean ----
        b = -Gamma @ (a_bar - z_opt)

        # ---- Variance partition ----
        V_lin  = float(b @ G @ b)
        HG = H @ G
        V_quad = 0.5 * float(np.trace(HG @ HG))         # = 0.5 sum mu_i^2

        denom = V_lin + V_quad
        A_g = V_lin / denom if denom > 0 else 0.0

        # ---- Empirical R^2 ----
        L_vec = delta_a @ b                             # (N,)
        z_centred = a - z_opt                           # (N, n_traits)
        l_vec = -0.5 * np.einsum("ij,jk,ik->i",
                                 z_centred, Gamma, z_centred)
        if np.var(L_vec) > 0 and np.var(l_vec) > 0:
            R2 = float(np.corrcoef(L_vec, l_vec)[0, 1] ** 2)
        else:
            R2 = float("nan")

        # ---- Pack the row ----
        row = {"gen": int(gen), "N": N}
        for k in range(n_traits):
            row[f"a_bar_{k+1}"] = float(a_bar[k])
            row[f"z_opt_{k+1}"] = float(z_opt[k])
            row[f"G_{k+1}{k+1}"] = float(G[k, k])
            row[f"eig_G_{k+1}"] = float(eig_G[k])
            row[f"mu_{k+1}"]    = float(mu[k])
            row[f"b_{k+1}"]     = float(b[k])
        row["b_norm"] = float(np.linalg.norm(b))
        row["V_lin"]  = V_lin
        row["V_quad"] = V_quad
        row["A_g"]    = A_g
        row["R2_empirical"] = R2
        row["Ag_minus_R2"]  = (A_g - R2) if np.isfinite(R2) else float("nan")

        rows.append(row)

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description=("Compute additive-channels diagnostics for any number "
                     "of traits, with optional time-varying optimum.")
    )
    p.add_argument("--bv-input",  required=True,
                   help="BV CSV from SLiM (a1, a2, ..., aN columns).")
    p.add_argument("--opt-input", default=None,
                   help="Optional optimum CSV (z_opt_1, z_opt_2, ...).  If "
                        "given, overrides --z-opt-static and lets z*(t) vary.")
    p.add_argument("--output",    required=True,
                   help="Path to write per-generation diagnostics CSV.")
    p.add_argument("--gammas",    required=True, type=float, nargs="+",
                   help="Diagonal of Gamma (length = n_traits).")
    p.add_argument("--z-opt-static", type=float, nargs="+", default=None,
                   help="Static optimum, length = n_traits.  Used iff "
                        "--opt-input is not given.")
    args = p.parse_args(argv)

    print(f"Reading BVs from {args.bv_input} ...")
    df_bv = pd.read_csv(args.bv_input)
    n_traits = detect_n_traits(df_bv)
    n_gens   = df_bv["generation"].nunique()
    print(f"  {len(df_bv):,} rows, {n_gens} generations, {n_traits} traits.")

    df_opt = None
    if args.opt_input is not None:
        print(f"Reading optimum from {args.opt_input} ...")
        df_opt = pd.read_csv(args.opt_input)
        print(f"  {len(df_opt)} rows.")

    print("Computing diagnostics ...")
    diags = compute_diagnostics_per_generation(
        df_bv, df_opt,
        gammas=np.array(args.gammas),
        z_opt_static=(np.array(args.z_opt_static)
                      if args.z_opt_static is not None else None),
    )

    diags.to_csv(args.output, index=False)
    print(f"Wrote {args.output}")

    # ---- Sanity printouts ----
    pd.options.display.float_format = "{:8.4f}".format

    eig_cols = [f"eig_G_{k+1}" for k in range(n_traits)]
    mu_cols  = [f"mu_{k+1}"    for k in range(n_traits)]
    short_cols = (["gen", "a_bar_1", "z_opt_1"] + eig_cols + mu_cols
                  + ["A_g", "R2_empirical"])

    print("\n--- First 5 generations ---")
    print(diags[short_cols].head(5).to_string(index=False))
    print("\n--- Last 5 generations ---")
    print(diags[short_cols].tail(5).to_string(index=False))

    median_abs = np.nanmedian(np.abs(diags["Ag_minus_R2"]))
    print(f"\nMedian |A_g - R^2| across all generations: {median_abs:.4f}")

    # Algebraic identity check: 2*V_quad should equal sum(mu_i^2)
    sum_mu_sq = sum(diags[f"mu_{k+1}"]**2 for k in range(n_traits))
    discrep = float(np.abs(2.0 * diags["V_quad"] - sum_mu_sq).max())
    print(f"Identity check: max |2*V_quad - sum(mu_i^2)| = {discrep:.2e}  "
          "(should be ~0)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
