# Appendix S5 — SLiM validation

This folder reproduces the three Appendix S5 figures of *Additive Channels in
Curved Fitness Landscapes*. It tests, in forward-time simulation, the paper's
central prediction: that the additivity index

```
A_g = V_lin / (V_lin + V_quad)
```

— an analytical quantity computed from the genetic covariance **G** and the
curvature of the fitness surface — equals the fraction of fitness variance that
a purely additive predictor explains, `R^2`. If the theory is right, `A_g` and
`R^2` should track each other generation by generation.

## The simulation

A diploid population of N = 2000 evolves under SLiM. Each individual carries four
quantitative traits, each built additively from 50 freely recombining QTL (200
loci in total), with no pleiotropy. Selection is stabilising toward an optimum
that drifts along trait 1 for the first 40 generations and then holds fixed; the
population is followed for 200 generations. This moving optimum is what makes the
test interesting: as directional selection compresses **G** (the Bulmer effect),
the linear and quadratic components of fitness variance shift, and `A_g` rises
and then falls — a trajectory invisible under a static optimum.

The run repeats across 20 stochastic replicates (random seeds 42–61), so the
result is a distribution, not a single draw. Full parameter justification is in
[`SIMULATION_DESIGN.md`](SIMULATION_DESIGN.md).

## Reproducing the figures

One script does everything:

```bash
./reproduce_appendix_s5.sh
```

This runs the 20 replicates, computes the per-generation diagnostics, builds the
three figures, and checks the result. It requires SLiM 5.2 on your `PATH` and
Python 3 with `numpy`, `pandas`, and `matplotlib` (`pip install -r requirements.txt`).

Useful variants:

| Command | What it does |
| --- | --- |
| `./reproduce_appendix_s5.sh --skip-slim` | rebuild the figures from the diagnostic CSVs already in `output/` — **no SLiM needed** |
| `./reproduce_appendix_s5.sh -j 20` | run the replicates in parallel, one worker per replicate |
| `./reproduce_appendix_s5.sh --clean --quick` | two-replicate smoke test (seconds; not the manuscript result) |

Parallel runs give identical numbers to serial ones: each replicate has a fixed
seed and is independent, and the figure step is order-independent.

## What counts as success

The figures are stochastic, and image bytes are not reproducible across machines,
so the script does not compare pixels. It asserts the two identities the appendix
actually claims:

- the across-replicate median `|A_g − R^2|` stays near **0.013**, and
- the algebraic identity `2·V_quad = Σ μ_i²` holds to numerical precision.

If either fails, the run reports an error rather than emitting a misleading
figure.

## What is here

```text
reproduce_appendix_s5.sh     one-command driver (full run, --skip-slim, parallel)
_run_one_replicate.sh        per-replicate worker invoked by the driver
slim_sim_n_traits.slim       the SLiM 5.2 model
compute_diagnostics.py       per-generation A_g, R^2, V_lin, V_quad, eigenvalues
make_appendix_s5_figures.py  aggregates replicates into the three figures + summary
SIMULATION_DESIGN.md         parameter choices and their rationale
requirements.txt             Python dependencies
output/                      per-replicate *_diag.csv and appendix_s5_summary.csv
```

The per-replicate diagnostic CSVs and the summary are kept here, which is why the
figures can be rebuilt with `--skip-slim` and no simulator. The heavy raw
breeding-value dumps a full run produces (`*_bv.csv`, `*_opt.csv`) are not stored
in the repository; they are regenerated on demand and archived with the data
release.

## Software

Simulations were run in SLiM 5.2 (Haller, Ralph & Messer, *Molecular Biology and
Evolution* 43(1):msaf313, 2026; <https://messerlab.org/slim>).
