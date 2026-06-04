# Appendix S5 — SLiM validation

This folder rebuilds the three Appendix S5 figures of *Additive Channels in
Curved Fitness Landscapes*. The figures test the paper's central prediction: that
the additivity index

```
A_g = V_lin / (V_lin + V_quad),
```

computed from the genetic covariance **G** and the curvature of the fitness
surface, equals `R^2`, the share of fitness variance that an additive predictor
explains. If the prediction holds, `A_g` and `R^2` track each other generation by
generation.

## The simulation

A diploid population of N = 2000 evolves under SLiM. Each individual carries four
traits, each built from 50 freely recombining QTL, 200 loci in all, with no
pleiotropy. Selection is stabilising toward an optimum that drifts along trait 1
for 40 generations and then holds; the population runs for 200 generations. The
moving optimum drives the test. As directional selection compresses **G** through
the Bulmer effect, the linear and quadratic shares of fitness variance shift, and
`A_g` rises and then falls. A static optimum hides this trajectory.

The simulation runs 20 replicates with seeds 42 to 61, so the result is a
distribution. `SIMULATION_DESIGN.md` justifies the parameters.

## Reproducing the figures

One script runs everything:

```bash
./reproduce_appendix_s5.sh
```

It runs the 20 replicates, computes the diagnostics, builds the figures, and
checks the result. It needs SLiM 5.2 on the `PATH` and Python 3 with `numpy`,
`pandas`, and `matplotlib` (`pip install -r requirements.txt`).

Variants:

| Command | Effect |
| --- | --- |
| `./reproduce_appendix_s5.sh --skip-slim` | rebuild the figures from the diagnostic CSVs in `output/`; no SLiM |
| `./reproduce_appendix_s5.sh -j 20` | run the replicates in parallel |
| `./reproduce_appendix_s5.sh --clean --quick` | two-replicate smoke test, not the manuscript result |

Each replicate has a fixed seed and runs independently, and the figure step does
not depend on order, so a parallel run gives the same numbers as a serial one.

## What the run checks

The figures are stochastic, and image bytes differ across machines, so the run
does not compare pixels. It checks two identities: the median `|A_g - R^2|` across
replicates stays near 0.013, and `2*V_quad = sum(mu_i^2)` holds to numerical
precision. If either fails, the run stops with an error.

## Contents

```text
reproduce_appendix_s5.sh     driver: full run, --skip-slim, parallel
_run_one_replicate.sh        per-replicate worker
slim_sim_n_traits.slim       the SLiM 5.2 model
compute_diagnostics.py       per-generation A_g, R^2, V_lin, V_quad, eigenvalues
make_appendix_s5_figures.py  builds the three figures and the summary
SIMULATION_DESIGN.md         parameters and rationale
requirements.txt             Python dependencies
output/                      per-replicate *_diag.csv and appendix_s5_summary.csv
```

The diagnostic CSVs and the summary stay in the repository, so `--skip-slim`
rebuilds the figures without a simulator. A full run also writes raw
breeding-value dumps (`*_bv.csv`, `*_opt.csv`); these are large, stay out of the
repository, and ship with the data release.

## Software

SLiM 5.2 (Haller, Ralph, and Messer, *Molecular Biology and Evolution*
43(1):msaf313, 2026; <https://messerlab.org/slim>).
