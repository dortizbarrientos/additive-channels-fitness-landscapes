# SLiM validation of the additive-channels framework

Proof-of-concept simulation accompanying *Additive Channels in Curved
Fitness Landscapes* (Ortiz-Barrientos & Cooper, GENETICS-2026-309068).

## What this validates

The framework's central identity, under Gaussian closure of the
breeding-value distribution:

$$\mathcal{A}_g \;=\; \frac{V_\text{lin}}{V_\text{lin} + V_\text{quad}}
                  \;=\; R^2 \,$$

where the right-hand side is the empirical squared correlation between
the linear-only predictor $L_i = \mathbf{b}^\top (\mathbf{a}_i - \bar{\mathbf{a}})$
and the full local log-fitness $\ell_i = \log W(\mathbf{a}_i)$,
computed across the simulated population.

The proof-of-concept exercises **one condition only** — weak,
sustained stabilising selection — to confirm that the simulation pipeline
is producing the expected dynamics before scaling to the full design
(four conditions × twenty replicates).

## What this does *not* do

* It does not yet test the full 2 × 2 condition grid (weak/strong ×
  sustained/episodic). That is the next step, after the PoC validates.
* It does not test non-quadratic fitness functions. The framework is a
  Taylor-expansion diagnostic, so a pure Gaussian quadratic landscape is
  the cleanest case for an identity check.
* It does not yet add new mutations during the simulation; standing
  variation only. (The `initializeMutationRate(0)` line in
  `slim_sim.slim` controls this.)
* It does not separate phenotype from breeding value (we set $E = 0$).
  Fitness acts directly on BVs. This isolates the BV→fitness curvature
  claim, which is exactly what the framework addresses.

## Files

```
slim_validation/
├── slim_sim.slim              # SLiM 5.2 forward simulation
├── compute_diagnostics.py     # reads SLiM dump, computes A_g and R^2
├── plot_trajectory.py         # quick-look figure (NOT the publication plot)
├── run_one.sh                 # end-to-end driver for the PoC
├── output/                    # SLiM dumps and per-generation diagnostics (gitignored)
├── figures/                   # plots (gitignored)
├── requirements.txt           # Python deps
└── README.md                  # this file
```

## Setup (one-time)

From a fresh terminal in this directory:

```bash
# Create and activate a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify SLiM is installed
which slim
slim -v
```

You should see `/usr/local/bin/slim` and `SLiM version 5.2` (or later).

## Run the proof of concept

With the venv activated and SLiM on `PATH`:

```bash
chmod +x run_one.sh        # one-time, makes the script executable
./run_one.sh
```

This runs three steps end-to-end:
1. SLiM simulation (200 generations, $N = 2000$, weak + sustained selection)
2. Python diagnostic computation (per-generation $\mathcal{A}_g$, $R^2$, and
   the variance partition)
3. Three-panel sanity-check figure

Expected wallclock on Apple Silicon: under one minute.

## What to look for in the figure

The figure (`figures/poc_rep_01_weak_sustained.png`) has three panels:

* **Panel A: identity check.** Two curves: the analytical $\mathcal{A}_g$
  and the empirical $R^2$. Under Gaussian closure they should overlap
  almost perfectly across the entire trajectory. Any visible separation
  is a signal that closure is breaking — interesting in the
  strong-selection condition we add later, but should NOT happen in
  this weak-selection PoC.
* **Panel B: variance compression.** $G_{11}$ should compress visibly
  during the first ~30 generations as selection acts; $G_{22}$ should
  compress less (because $\gamma_2 < \gamma_1$).
* **Panel C: gradient magnitude.** $|\mathbf{b}|$ starts at
  $\gamma_1 \cdot 2 = 0.20$ and decays toward zero as the population
  mean approaches the optimum. The decay should be roughly exponential
  in the early phase.

If those three behaviours show up, the simulation pipeline is working
and we can scale to the full design.

## Reading the diagnostics CSV

`output/diag_*.csv` columns:

| Column | Meaning |
| --- | --- |
| `gen` | Generation index |
| `N` | Number of individuals at this generation |
| `a_bar_1`, `a_bar_2` | Population mean breeding value (per trait) |
| `G_11`, `G_22`, `G_12` | Empirical genetic covariance matrix |
| `b_1`, `b_2`, `b_norm` | Analytical log-fitness gradient at $\bar{\mathbf{a}}$ |
| `V_lin`, `V_quad` | Variance partition |
| `A_g` | Analytical additivity index |
| `R2_empirical` | Empirical $R^2$ between linear-only and full log-fitness |
| `Ag_minus_R2` | Diagnostic: should be $\approx 0$ under Gaussian closure |

## Citation

If you use this code, please cite the manuscript:

Ortiz-Barrientos, D. and Cooper, M. (2026).
*Additive Channels in Curved Fitness Landscapes.*
Manuscript GENETICS-2026-309068.

Code is released under MIT licence. See `LICENSE` in the parent repo.
