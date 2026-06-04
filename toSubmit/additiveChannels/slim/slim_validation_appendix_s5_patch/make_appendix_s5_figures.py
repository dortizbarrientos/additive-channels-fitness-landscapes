#!/usr/bin/env python3
"""
make_appendix_s5_figures.py
===========================

Aggregate the 20 SLiM validation replicates for Appendix S5 and generate
exactly the three figure files referenced by the manuscript:

    multiseed_4trait_moving.png
    cv_4trait_moving.png
    geom_invariants_4trait_moving.png

The script expects one diagnostic CSV per replicate, as produced by
compute_diagnostics.py. It also writes a small numerical summary CSV so the
values in the manuscript can be checked without reading figures by eye.
"""

from __future__ import annotations

import argparse
import glob
import os
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def read_replicates(pattern: str) -> pd.DataFrame:
    paths = sorted(glob.glob(pattern))
    if not paths:
        raise SystemExit(f"No diagnostic CSV files matched: {pattern}")

    frames = []
    for idx, path in enumerate(paths, start=1):
        df = pd.read_csv(path)
        if "gen" not in df.columns:
            raise SystemExit(f"{path} has no 'gen' column")
        df = df.copy()
        df["rep"] = idx
        df["source_file"] = os.path.basename(path)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def trait_count(df: pd.DataFrame, prefix: str = "eig_G_") -> int:
    cols = [c for c in df.columns if c.startswith(prefix) and c[len(prefix):].isdigit()]
    if not cols:
        raise SystemExit(f"No {prefix} columns found")
    idx = sorted(int(c[len(prefix):]) for c in cols)
    if idx != list(range(1, len(idx) + 1)):
        raise SystemExit(f"Non-consecutive {prefix} columns: {idx}")
    return len(idx)


def add_invariants(df: pd.DataFrame) -> pd.DataFrame:
    n = trait_count(df, "eig_G_")
    eig_cols = [f"eig_G_{i}" for i in range(1, n + 1)]
    eig = df[eig_cols].to_numpy(float)
    eig = np.clip(eig, 1e-15, None)
    tr = eig.sum(axis=1)
    df = df.copy()
    df["trace_G"] = tr
    df["keff"] = (tr * tr) / np.sum(eig * eig, axis=1)
    df["kappa_G"] = eig[:, 0] / eig[:, -1]
    # Internal check from the whitened-coordinate identity: 2 Vquad = sum_i mu_i^2
    mu_cols = [f"mu_{i}" for i in range(1, n + 1) if f"mu_{i}" in df.columns]
    if len(mu_cols) == n and "V_quad" in df.columns:
        mu = df[mu_cols].to_numpy(float)
        df["twoVquad_minus_sum_mu2_abs"] = np.abs(2.0 * df["V_quad"].to_numpy(float) - np.sum(mu * mu, axis=1))
    return df


def summarise_by_generation(df: pd.DataFrame, columns: Iterable[str]) -> dict[str, pd.DataFrame]:
    out = {}
    g = df.groupby("gen", sort=True)
    for q, name in [(0.05, "p05"), (0.50, "p50"), (0.95, "p95")]:
        out[name] = g[list(columns)].quantile(q).reset_index()
    out["mean"] = g[list(columns)].mean().reset_index()
    out["sd"] = g[list(columns)].std(ddof=1).reset_index()
    return out


def cv_by_generation(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    g = df.groupby("gen", sort=True)[list(columns)]
    mean = g.mean()
    sd = g.std(ddof=1)
    cv = sd / mean.abs().replace(0, np.nan)
    cv = cv.reset_index()
    return cv


def line_with_band(ax, gen, mean, p05, p95, label, linewidth=2.0, alpha=0.18):
    ax.plot(gen, mean, linewidth=linewidth, label=label)
    ax.fill_between(gen, p05, p95, alpha=alpha, linewidth=0)


def style(ax):
    ax.grid(True, alpha=0.25, linewidth=0.6)
    for sp in ax.spines.values():
        sp.set_alpha(0.35)


def make_fig_s51(df: pd.DataFrame, out: Path) -> None:
    n = trait_count(df, "eig_G_")
    cols = ["A_g", "R2_empirical", "b_norm"] + [f"eig_G_{i}" for i in range(1, n + 1)]
    summ = summarise_by_generation(df, cols)
    gen = summ["mean"]["gen"].to_numpy()

    rep1 = df[df["rep"] == df["rep"].min()].sort_values("gen")

    fig, axes = plt.subplots(1, 3, figsize=(14.2, 4.2))

    ax = axes[0]
    ax.plot(gen, summ["mean"]["A_g"], label=r"$\mathcal{A}_g$ (mean)", linewidth=2.2)
    ax.fill_between(gen, summ["p05"]["A_g"], summ["p95"]["A_g"], alpha=0.16, linewidth=0)
    ax.plot(gen, summ["mean"]["R2_empirical"], linestyle="--", label=r"$R^2$ (mean)", linewidth=2.0)
    ax.plot(rep1["gen"], rep1["A_g"], color="0.55", alpha=0.65, linewidth=1.1, label="rep 1 $A_g$")
    ax.set_title(r"Identity check: $\mathcal{A}_g$ vs $R^2$")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Value")
    ax.set_ylim(-0.03, 1.03)
    ax.legend(frameon=False, fontsize=8)
    style(ax)

    ax = axes[1]
    for i in range(1, n + 1):
        c = f"eig_G_{i}"
        ax.plot(gen, summ["mean"][c], linewidth=2.0, label=fr"$\lambda_{{{i}}}(G)$")
        ax.fill_between(gen, summ["p05"][c], summ["p95"][c], alpha=0.12, linewidth=0)
    ax.set_title(r"Genetic variance (4 traits, mean $\pm$ 5--95%)")
    ax.set_xlabel("Generation")
    ax.set_ylabel(r"Eigenvalues of $G$")
    ax.legend(frameon=False, fontsize=8)
    style(ax)

    ax = axes[2]
    ax.plot(gen, summ["mean"]["b_norm"], linewidth=2.2, label=r"$|b|$ (mean)")
    ax.fill_between(gen, summ["p05"]["b_norm"], summ["p95"]["b_norm"], alpha=0.16, linewidth=0)
    ax.plot(rep1["gen"], rep1["b_norm"], color="0.55", alpha=0.65, linewidth=1.1, label="rep 1")
    ax.set_title("Gradient magnitude")
    ax.set_xlabel("Generation")
    ax.set_ylabel(r"$|b|$")
    ax.legend(frameon=False, fontsize=8)
    style(ax)

    fig.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def make_fig_s52(df: pd.DataFrame, out: Path, peak_gen: int) -> None:
    n = trait_count(df, "eig_G_")
    cols = ["A_g", "R2_empirical", "V_lin", "V_quad", "b_norm"]
    cols += [f"G_{i}{i}" for i in range(1, n + 1) if f"G_{i}{i}" in df.columns]
    cols += [f"eig_G_{i}" for i in range(1, n + 1)]
    cols += [f"mu_{i}" for i in range(1, n + 1) if f"mu_{i}" in df.columns]
    cv = cv_by_generation(df, cols)

    fig, axes = plt.subplots(1, 2, figsize=(14.2, 4.4), gridspec_kw={"width_ratios": [1.35, 1]})

    ax = axes[0]
    groups = {
        "framework": ["A_g", "R2_empirical", "V_lin", "V_quad", "b_norm"],
        "trait diagonals": [f"G_{i}{i}" for i in range(1, n + 1) if f"G_{i}{i}" in cv.columns],
        "sorted eigenvalues": [f"eig_G_{i}" for i in range(1, n + 1)],
        "mu": [f"mu_{i}" for i in range(1, n + 1) if f"mu_{i}" in cv.columns],
    }
    for _, members in groups.items():
        for c in members:
            if c in cv.columns:
                ax.plot(cv["gen"], cv[c], linewidth=1.6, alpha=0.86, label=c)
    ax.axvline(peak_gen, linestyle=":", color="0.45", linewidth=1.0)
    ax.text(peak_gen + 2, ax.get_ylim()[1] * 0.93, f"peak\n(gen {peak_gen})", fontsize=8, color="0.35")
    ax.set_title("Coefficient of variation across replicates")
    ax.set_xlabel("Generation")
    ax.set_ylabel(r"CV = sd / |mean|")
    ax.set_ylim(bottom=0)
    ax.legend(frameon=False, fontsize=7, ncol=2, loc="upper right")
    style(ax)

    ax = axes[1]
    row = cv.loc[cv["gen"] == peak_gen]
    if row.empty:
        raise SystemExit(f"Peak generation {peak_gen} not present in diagnostics")
    vals = row.iloc[0][cols].astype(float).sort_values(ascending=True)
    y = np.arange(len(vals))
    ax.barh(y, vals.values)
    ax.set_yticks(y)
    ax.set_yticklabels(vals.index, fontsize=8)
    ax.set_xlabel("CV across replicates")
    ax.set_title(f"CV at peak (gen {peak_gen})")
    for yy, v in zip(y, vals.values):
        ax.text(v + max(vals.values) * 0.015, yy, f"{v:.3f}", va="center", fontsize=7)
    style(ax)

    fig.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def make_fig_s53(df: pd.DataFrame, out: Path, peak_gen: int) -> None:
    n = trait_count(df, "eig_G_")
    cols = ["keff", "kappa_G"] + [f"eig_G_{i}" for i in range(1, n + 1)]
    summ = summarise_by_generation(df, ["keff", "kappa_G"])
    gen = summ["mean"]["gen"].to_numpy()
    rep1 = df[df["rep"] == df["rep"].min()].sort_values("gen")

    fig = plt.figure(figsize=(14.2, 7.0))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 0.85])
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, :])

    ax = ax1
    ax.plot(gen, summ["mean"]["keff"], linewidth=2.2, label=r"$k_{eff}$ (mean)")
    ax.fill_between(gen, summ["p05"]["keff"], summ["p95"]["keff"], alpha=0.16, linewidth=0)
    ax.plot(rep1["gen"], rep1["keff"], color="0.55", alpha=0.65, linewidth=1.1, label="rep 1")
    ax.axhline(n, linestyle=":", color="0.45", linewidth=1.0, label=f"isotropic ({n})")
    ax.set_title("Effective dimension of G over time")
    ax.set_xlabel("Generation")
    ax.set_ylabel(r"$k_{eff} = (trG)^2/tr(G^2)$")
    ax.legend(frameon=False, fontsize=8)
    style(ax)

    ax = ax2
    ax.plot(gen, summ["mean"]["kappa_G"], linewidth=2.2, label=r"$\lambda_{max}/\lambda_{min}$ (mean)")
    ax.fill_between(gen, summ["p05"]["kappa_G"], summ["p95"]["kappa_G"], alpha=0.16, linewidth=0)
    ax.plot(rep1["gen"], rep1["kappa_G"], color="0.55", alpha=0.65, linewidth=1.1, label="rep 1")
    ax.set_yscale("log")
    ax.set_title("Anisotropy of G over time")
    ax.set_xlabel("Generation")
    ax.set_ylabel(r"$\lambda_{max}/\lambda_{min}$")
    ax.legend(frameon=False, fontsize=8)
    style(ax)

    cv = cv_by_generation(df, cols)
    row = cv.loc[cv["gen"] == peak_gen]
    if row.empty:
        raise SystemExit(f"Peak generation {peak_gen} not present in diagnostics")
    row = row.iloc[0]
    bar_cols = ["keff", "kappa_G"] + [f"eig_G_{i}" for i in range(1, n + 1)]
    vals = pd.Series({c: float(row[c]) for c in bar_cols})
    y = np.arange(len(vals))
    ax3.barh(y, vals.values)
    ax3.set_yticks(y)
    ax3.set_yticklabels(vals.index, fontsize=9)
    ax3.set_xlabel("CV across replicates")
    ax3.set_title(f"Across-replicate CV at peak (gen {peak_gen}): geometric invariants vs individual eigenvalues")
    eig_med = float(np.nanmedian([row[f"eig_G_{i}"] for i in range(1, n + 1)]))
    ax3.axvline(eig_med, linestyle=":", color="0.45", linewidth=1.0)
    ax3.text(eig_med, len(vals) - 0.3, f" median eig CV = {eig_med:.3f}", fontsize=8, color="0.35")
    for yy, v in zip(y, vals.values):
        ax3.text(v + max(vals.values) * 0.015, yy, f"{v:.3f}", va="center", fontsize=8)
    style(ax3)

    fig.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight")
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def make_summary(df: pd.DataFrame, peak_gen: int) -> pd.DataFrame:
    n_reps = df["rep"].nunique()
    n_gens = df["gen"].nunique()
    peak = df[df["gen"] == peak_gen]
    eig_cols = [c for c in df.columns if c.startswith("eig_G_")]

    records = [
        ("n_replicates", n_reps),
        ("n_generations", n_gens),
        ("min_generation", int(df["gen"].min())),
        ("max_generation", int(df["gen"].max())),
        ("median_abs_Ag_minus_R2_all", float(np.nanmedian(np.abs(df["Ag_minus_R2"])))),
        ("max_abs_Ag_minus_R2_all", float(np.nanmax(np.abs(df["Ag_minus_R2"])))),
        ("max_abs_2Vquad_minus_sum_mu2", float(np.nanmax(df.get("twoVquad_minus_sum_mu2_abs", pd.Series([np.nan]))))),
        ("mean_Ag_peak", float(peak["A_g"].mean())),
        ("mean_R2_peak", float(peak["R2_empirical"].mean())),
        ("mean_b_norm_peak", float(peak["b_norm"].mean())),
        ("mean_trace_G_gen1", float(df.loc[df["gen"] == df["gen"].min(), "trace_G"].mean())),
        ("mean_trace_G_gen200", float(df.loc[df["gen"] == df["gen"].max(), "trace_G"].mean())),
        ("mean_keff_gen1", float(df.loc[df["gen"] == df["gen"].min(), "keff"].mean())),
        ("mean_keff_peak", float(peak["keff"].mean())),
        ("mean_kappa_peak", float(peak["kappa_G"].mean())),
        ("mean_kappa_gen200", float(df.loc[df["gen"] == df["gen"].max(), "kappa_G"].mean())),
    ]

    cv_cols = ["A_g", "R2_empirical", "keff", "kappa_G"] + eig_cols
    cv = cv_by_generation(df, cv_cols)
    row = cv.loc[cv["gen"] == peak_gen].iloc[0]
    for c in cv_cols:
        records.append((f"CV_{c}_peak", float(row[c])))

    return pd.DataFrame(records, columns=["quantity", "value"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--diag-glob", required=True, help="Glob for per-replicate diagnostic CSVs")
    ap.add_argument("--output-dir", default="figures")
    ap.add_argument("--peak-gen", type=int, default=40)
    ap.add_argument("--summary-csv", default="output/appendix_s5_summary.csv")
    args = ap.parse_args()

    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    Path(args.summary_csv).parent.mkdir(parents=True, exist_ok=True)

    df = add_invariants(read_replicates(args.diag_glob))

    make_fig_s51(df, outdir / "multiseed_4trait_moving.png")
    make_fig_s52(df, outdir / "cv_4trait_moving.png", args.peak_gen)
    make_fig_s53(df, outdir / "geom_invariants_4trait_moving.png", args.peak_gen)

    summary = make_summary(df, args.peak_gen)
    summary.to_csv(args.summary_csv, index=False)

    print(f"Read {df['rep'].nunique()} replicate(s), {df['gen'].nunique()} generations.")
    print(f"Median |A_g - R2| = {summary.loc[summary.quantity=='median_abs_Ag_minus_R2_all', 'value'].iloc[0]:.6g}")
    print(f"Wrote {outdir / 'multiseed_4trait_moving.png'}")
    print(f"Wrote {outdir / 'cv_4trait_moving.png'}")
    print(f"Wrote {outdir / 'geom_invariants_4trait_moving.png'}")
    print(f"Wrote {args.summary_csv}")


if __name__ == "__main__":
    main()
