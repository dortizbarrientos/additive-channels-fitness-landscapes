"""
plot_trajectory.py
==================

Quick-look figure showing the framework's identity check and the underlying
dynamics.  Works for any number of traits (auto-detected from the
diagnostics CSV).

Three panels:
  Panel A : A_g(t) and empirical R^2(t) overlaid -- the central identity check.
  Panel B : Eigenvalues of G over time (one curve per trait).
            Shows variance compression direction-by-direction.
  Panel C : |b|(t) -- gradient magnitude.

USAGE
-----
    python plot_trajectory.py \
        --input  output/diag_rep_01.csv \
        --output figures/poc_rep_01.png
"""

from __future__ import annotations

import argparse
import sys

import matplotlib.pyplot as plt
import pandas as pd


def detect_n_traits_from_diag(df: pd.DataFrame) -> int:
    """Count eig_G_K columns to determine how many traits are present."""
    cols = [c for c in df.columns
            if c.startswith("eig_G_") and c[6:].isdigit()]
    return len(cols)


def make_plot(diag_path: str, out_path: str) -> None:
    d = pd.read_csv(diag_path)
    n_traits = detect_n_traits_from_diag(d)
    if n_traits == 0:
        sys.exit("ERROR: no eig_G_K columns found in diagnostics CSV.")

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4))

    # -------- Panel A: A_g vs R^2 -------------------------------------
    ax = axes[0]
    ax.plot(d["gen"], d["A_g"],
            label=r"$\mathcal{A}_g$ (analytical)",
            color="#1f77b4", linewidth=2.0)
    ax.plot(d["gen"], d["R2_empirical"],
            label=r"$R^2$ (empirical)",
            color="#d62728", linewidth=2.0, linestyle="--")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Value")
    ax.set_title(r"Identity check: $\mathcal{A}_g$ vs $R^2$")
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc="upper right", frameon=False)
    ax.grid(alpha=0.3)

    # -------- Panel B: eigenvalues of G over time ---------------------
    ax = axes[1]
    palette = ["#27ae60", "#e67e22", "#8e44ad", "#16a085",
               "#c0392b", "#2980b9"]
    for k in range(n_traits):
        ax.plot(d["gen"], d[f"eig_G_{k+1}"],
                label=fr"$\lambda_{{{k+1}}}(G)$",
                color=palette[k % len(palette)], linewidth=2.0)
    ax.set_xlabel("Generation")
    ax.set_ylabel(r"Eigenvalues of $G$")
    title = ("Genetic variance over time"
             if n_traits == 2 else
             f"Genetic variance over time ({n_traits} traits)")
    ax.set_title(title)
    ax.legend(loc="upper right", frameon=False, fontsize=9)
    ax.grid(alpha=0.3)

    # -------- Panel C: |b| -------------------------------------------
    ax = axes[2]
    ax.plot(d["gen"], d["b_norm"],
            color="#9467bd", linewidth=2.0)
    ax.set_xlabel("Generation")
    ax.set_ylabel(r"$|\vec{b}|$")
    ax.set_title("Gradient magnitude")
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Wrote {out_path}")


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input",  required=True,
                   help="Diagnostics CSV from compute_diagnostics.py.")
    p.add_argument("--output", default="figures/poc_trajectory.png",
                   help="Output figure path.")
    args = p.parse_args(argv)

    make_plot(args.input, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
