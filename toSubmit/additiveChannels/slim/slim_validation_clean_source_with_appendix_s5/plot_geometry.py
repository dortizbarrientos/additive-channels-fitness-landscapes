"""
plot_geometry.py
================

A 2x3 figure visualising the framework's geometric story over a simulated
trajectory.  GENERALISED to handle:

  * Any number of traits (n_traits auto-detected from the diagnostics CSV).
    The BV-cloud snapshots in the top row use the FIRST TWO traits (a1, a2),
    which is the most informative pair when drift acts on trait 1; for
    n_traits > 2, the title clarifies what's being shown.
  * A time-varying optimum, read from --opt-input.  If --opt-input is not
    given, --z-opt is used as a constant (the original 2-trait PoC).

TOP ROW -- THREE BV CLOUD SNAPSHOTS (in trait 1 vs trait 2):
    Each panel shows the population's BV cloud, fitness contours of the
    SLICE z* = (z*_1(t), z*_2(t), 0, 0, ...), the optimum z*(t) as a star,
    population mean as +, and the 95% confidence ellipse of G's
    (a1, a2) sub-block.  Across the three panels, you see G contracting
    and -- in moving-optimum scenarios -- the optimum sliding too.

BOTTOM ROW -- THREE DYNAMICS PANELS:
    Bottom-left  : ALL eigenvalues of G over time (one curve per trait).
    Bottom-mid   : ALL mu_i = eigenvalues of Gamma G over time.
    Bottom-right : V_lin and V_quad on log scale.

USAGE
-----
  # Static-optimum 2-trait case (the simple PoC)
  python plot_geometry.py \
      --bv-input    output/rep_01_bv.csv \
      --diag-input  output/diag_rep_01.csv \
      --output      figures/geometry_rep_01.png \
      --gammas      0.10 0.05 \
      --z-opt       -2.0 0.0 \
      --snapshot-gens 1 5 100

  # Moving-optimum n-trait case (the extended scenario)
  python plot_geometry.py \
      --bv-input    output/rep_01_4t_bv.csv \
      --diag-input  output/diag_rep_01_4t.csv \
      --opt-input   output/rep_01_4t_opt.csv \
      --output      figures/geometry_rep_01_4t.png \
      --gammas      0.10 0.05 0.04 0.03 \
      --snapshot-gens 1 40 200
"""

from __future__ import annotations

import argparse
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Ellipse


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def detect_n_traits_from_diag(df_diag: pd.DataFrame) -> int:
    """Count eig_G_K columns to determine how many traits are present."""
    cols = [c for c in df_diag.columns
            if c.startswith("eig_G_") and c[6:].isdigit()]
    return len(cols)


def add_ellipse(ax, mean, cov, n_std=2.45, **kwargs):
    """
    Add a 2D covariance ellipse.

    n_std=2.45 corresponds to the 95% confidence region for a 2D Gaussian
    (chi-squared with 2 dof, 0.95 quantile = 5.99, sqrt = 2.448).
    """
    eigvals, eigvecs = np.linalg.eigh(cov)
    order = eigvals.argsort()[::-1]
    eigvals, eigvecs = eigvals[order], eigvecs[:, order]
    angle = np.degrees(np.arctan2(eigvecs[1, 0], eigvecs[0, 0]))
    width  = 2 * n_std * np.sqrt(max(eigvals[0], 0.0))
    height = 2 * n_std * np.sqrt(max(eigvals[1], 0.0))
    ell = Ellipse(xy=mean, width=width, height=height, angle=angle,
                  fill=False, linewidth=2.2, **kwargs)
    ax.add_patch(ell)


def plot_bv_snapshot(ax, df_bv, gen, gammas, z_opt_full, axlim, show_ylabel):
    """
    Single panel: BV scatter (traits 1 & 2) + fitness contours +
    G-ellipse on the (a1, a2) sub-block + optimum star at z*(gen).

    `z_opt_full` is the full-length z*(gen) vector; we use only its first
    two components for the 2D slice plotted here.
    """
    sub = df_bv[df_bv["generation"] == gen]
    a = sub[["a1", "a2"]].to_numpy()
    a_bar = a.mean(axis=0)
    G = np.cov(a, rowvar=False, ddof=1)

    z1, z2 = z_opt_full[0], z_opt_full[1]
    g1, g2 = gammas[0], gammas[1]

    # ---- Background fitness contours (slice with all other a_k = 0) ----
    a1_grid = np.linspace(*axlim[0], 80)
    a2_grid = np.linspace(*axlim[1], 80)
    A1, A2 = np.meshgrid(a1_grid, a2_grid)
    log_W = -0.5 * (g1 * (A1 - z1)**2 + g2 * (A2 - z2)**2)
    levels = np.linspace(-2.5, 0, 9)
    ax.contour(A1, A2, log_W, levels=levels, colors="gray",
               alpha=0.45, linewidths=0.6)

    # ---- BV scatter (subsampled if N is large) ----
    if len(a) > 1500:
        idx = np.random.default_rng(0).choice(len(a), 1500, replace=False)
        a_plot = a[idx]
    else:
        a_plot = a
    ax.scatter(a_plot[:, 0], a_plot[:, 1], s=3, alpha=0.30,
               color="#3a6ea5", edgecolors="none", zorder=2)

    # ---- 95% G-ellipse ----
    add_ellipse(ax, a_bar, G, n_std=2.45, color="#c0392b")

    # ---- Population mean ----
    ax.scatter(a_bar[0], a_bar[1], marker="+", s=90,
               color="#c0392b", linewidths=2.2, zorder=5)

    # ---- Optimum at this generation ----
    ax.scatter(z1, z2, marker="*", s=260, color="#f1c40f",
               edgecolor="black", linewidths=1.0, zorder=10)

    ax.set_xlim(*axlim[0])
    ax.set_ylim(*axlim[1])
    ax.set_aspect("equal")
    ax.set_title(f"Generation {gen}", fontsize=11)
    ax.set_xlabel(r"$a_1$ (trait 1)")
    if show_ylabel:
        ax.set_ylabel(r"$a_2$ (trait 2)")


def compute_axlim(df_bv: pd.DataFrame, snapshot_gens) -> list:
    """
    Compute axis limits for the BV cloud snapshots so all snapshots fit
    comfortably with shared axes (otherwise the contraction story doesn't
    read visually).
    """
    sub = df_bv[df_bv["generation"].isin(snapshot_gens)]
    a1 = sub["a1"].to_numpy()
    a2 = sub["a2"].to_numpy()

    # Pad by 15% of range plus a small absolute margin
    rng_x = a1.max() - a1.min()
    rng_y = a2.max() - a2.min()
    pad_x = 0.15 * rng_x + 0.5
    pad_y = 0.15 * rng_y + 0.5
    return [
        (a1.min() - pad_x, a1.max() + pad_x),
        (a2.min() - pad_y, a2.max() + pad_y),
    ]


# ---------------------------------------------------------------------------
#  Main
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--bv-input",   required=True,
                   help="BV CSV from SLiM (a1, a2, ..., aN columns).")
    p.add_argument("--diag-input", required=True,
                   help="Diagnostics CSV from compute_diagnostics.py.")
    p.add_argument("--opt-input",  default=None,
                   help="Optional time-varying optimum CSV.  If given, the "
                        "optimum star moves between snapshots.")
    p.add_argument("--output",     required=True,
                   help="Output figure path.")
    p.add_argument("--gammas", type=float, nargs="+", required=True,
                   help="Diagonal of Gamma (length = n_traits).")
    p.add_argument("--z-opt",  type=float, nargs="+", default=None,
                   help="Static optimum (length = n_traits).  Used iff "
                        "--opt-input is not given.")
    p.add_argument("--snapshot-gens", type=int, nargs=3, default=[1, 5, 100],
                   help="Three generations to snapshot in the top row.")
    args = p.parse_args(argv)

    # ---- Load data ----
    print(f"Reading {args.bv_input} ...")
    df_bv = pd.read_csv(args.bv_input)
    print(f"Reading {args.diag_input} ...")
    df_diag = pd.read_csv(args.diag_input)

    n_traits = detect_n_traits_from_diag(df_diag)
    print(f"  Detected n_traits = {n_traits}")

    if len(args.gammas) != n_traits:
        sys.exit(f"ERROR: --gammas has {len(args.gammas)} entries but "
                 f"data has {n_traits} traits.")

    # Sanity: requested snapshot generations must exist
    available = set(df_bv["generation"].unique())
    for g in args.snapshot_gens:
        if g not in available:
            sys.exit(f"ERROR: snapshot generation {g} not in BV data "
                     f"(range {df_bv['generation'].min()}-"
                     f"{df_bv['generation'].max()}).")

    # ---- Resolve z* per snapshot ----
    if args.opt_input is not None:
        df_opt = pd.read_csv(args.opt_input)
        opt_cols = [f"z_opt_{k+1}" for k in range(n_traits)]
        z_opt_at = {}
        for g in args.snapshot_gens:
            row = df_opt[df_opt["generation"] == g]
            if row.empty:
                sys.exit(f"ERROR: optimum CSV missing row for gen {g}.")
            z_opt_at[g] = row[opt_cols].iloc[0].to_numpy(dtype=float)
    else:
        if args.z_opt is None:
            sys.exit("ERROR: must provide either --opt-input or --z-opt.")
        if len(args.z_opt) != n_traits:
            sys.exit(f"ERROR: --z-opt has {len(args.z_opt)} entries but "
                     f"data has {n_traits} traits.")
        z_opt_static = np.array(args.z_opt, dtype=float)
        z_opt_at = {g: z_opt_static for g in args.snapshot_gens}

    # ------------------------------------------------------------------
    # Build the figure
    # ------------------------------------------------------------------
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 9.0))

    # Shared axis limits computed from the actual BV data
    axlim = compute_axlim(df_bv, args.snapshot_gens)

    # ===== TOP ROW: BV cloud snapshots =====
    for col, gen in enumerate(args.snapshot_gens):
        plot_bv_snapshot(
            axes[0, col],
            df_bv, gen,
            args.gammas,
            z_opt_at[gen],
            axlim,
            show_ylabel=(col == 0),
        )

    # ===== BOTTOM-LEFT: ALL eigenvalues of G =====
    ax = axes[1, 0]
    palette_G = ["#27ae60", "#e67e22", "#8e44ad", "#16a085",
                 "#2980b9", "#c0392b"]
    for k in range(n_traits):
        ax.plot(df_diag["gen"], df_diag[f"eig_G_{k+1}"],
                color=palette_G[k % len(palette_G)], linewidth=2.0,
                label=fr"$\lambda_{{{k+1}}}(G)$")
    ax.set_xlabel("Generation")
    ax.set_ylabel(r"Eigenvalues of $G$")
    ax.set_title("$G$ eigenvalues  (variance compression)")
    ax.legend(frameon=False, loc="upper right", fontsize=9, ncol=1)
    ax.grid(alpha=0.3)

    # ===== BOTTOM-MID: ALL mu_i = eigenvalues of Gamma G =====
    ax = axes[1, 1]
    palette_mu = ["#8e44ad", "#16a085", "#d35400", "#34495e",
                  "#7f8c8d", "#2c3e50"]
    for k in range(n_traits):
        ax.plot(df_diag["gen"], df_diag[f"mu_{k+1}"],
                color=palette_mu[k % len(palette_mu)], linewidth=2.0,
                label=fr"$\mu_{{{k+1}}}$")
    ax.set_xlabel("Generation")
    ax.set_ylabel(r"Eigenvalues of $\Gamma G$  ($\mu_i$)")
    ax.set_title(r"Curvature mass per direction  "
                 r"($\sum \mu_i^2 = 2\,V_{\rm quad}$)")
    ax.legend(frameon=False, loc="upper right", fontsize=9, ncol=1)
    ax.grid(alpha=0.3)

    # ===== BOTTOM-RIGHT: V_lin and V_quad on log scale =====
    ax = axes[1, 2]
    eps = 1e-10
    ax.semilogy(df_diag["gen"], df_diag["V_lin"].clip(lower=eps),
                color="#2980b9", linewidth=2.0,
                label=r"$V_{\rm lin} = b^\top G b$")
    ax.semilogy(df_diag["gen"], df_diag["V_quad"].clip(lower=eps),
                color="#c0392b", linewidth=2.0,
                label=r"$V_{\rm quad} = \frac{1}{2}\,{\rm tr}\,(HG)^2$")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Variance (log scale)")
    ax.set_title("Variance partition")
    ax.legend(frameon=False, loc="upper right")
    ax.grid(alpha=0.3, which="both")

    # ---- Suptitle reflects the scenario ----
    if args.opt_input is not None:
        suptitle = (f"Geometry of adaptation: $G$ contracting against a "
                    f"MOVING optimum  ($n={n_traits}$ traits)")
    else:
        suptitle = (f"Geometry of adaptation: $G$ contracting against a "
                    f"fixed curvature surface  ($n={n_traits}$ traits)")
    if n_traits > 2:
        suptitle += "\n(top row: trait 1 vs trait 2 slice)"
    fig.suptitle(suptitle, fontsize=13, y=1.00)

    plt.tight_layout()
    plt.savefig(args.output, dpi=150, bbox_inches="tight")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
