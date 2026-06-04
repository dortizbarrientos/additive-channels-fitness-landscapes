# SLiM validation audit against Appendix S5

## Bottom line

The uploaded `slim_validation.zip` contains the essential SLiM and Python machinery for the Appendix S5 validation, especially the four-trait moving-optimum simulation and the per-generation diagnostic calculation. The existing single-replicate output reproduces the key numerical identity reported in the manuscript for one replicate: median `|A_g - R^2| = 0.0131`, and the algebraic check `2 V_quad = sum(mu_i^2)` holds to numerical precision for the recomputed diagnostics.

However, the uploaded bundle does **not yet** contain the full production layer needed to reproduce Appendix S5 exactly as written. Appendix S5 describes 20 stochastic replicates with seeds 42..61 and three manuscript figure files: `multiseed_4trait_moving.png`, `cv_4trait_moving.png`, and `geom_invariants_4trait_moving.png`. The uploaded bundle contains only one four-trait replicate (`rep_01_4trait_moving_*`) and two single-replicate figures (`poc_rep_01_4trait_moving.png`, `geometry_rep_01_4trait_moving.png`). It lacks a 20-replicate driver and a multi-seed aggregation/plotting script.

I prepared a small reproduction patch that adds those missing pieces.

## What Appendix S5 requires

From the revised manuscript, Appendix S5 requires the following computational objects:

- Forward-time individual-based simulations in SLiM.
- Explicit-genome diploid population, fixed `N = 2000`.
- Four traits, 50 QTL per trait, 200 QTL total.
- Per-trait effect SDs `sigma = (0.346, 0.283, 0.200, 0.141)`.
- Stabilising-selection curvature `gamma = (0.10, 0.05, 0.04, 0.03)`.
- Moving optimum on trait 1 only, velocity `0.3` per generation, endpoint `(12, 0, 0, 0)`.
- 200 generations.
- 20 stochastic replicates using seeds `42..61`.
- Per-generation computation of `V_lin`, `V_quad`, `A_g`, empirical `R^2`, eigenvalues of `G`, and eigenvalues `mu_i` of `Gamma G`.
- Three appendix figures:
  - `multiseed_4trait_moving.png`
  - `cv_4trait_moving.png`
  - `geom_invariants_4trait_moving.png`

## What the uploaded ZIP already contains

### Good matches

The main simulation source `slim_sim_n_traits.slim` already matches the core Appendix S5 design:

- Configurable `N_TRAITS`, default `4`.
- Default `N = 2000`, `GENS = 200`, `L_PER_TRAIT = 50`.
- Default `SIGMAS = c(0.346, 0.283, 0.200, 0.141)`.
- Default `GAMMAS = c(0.10, 0.05, 0.04, 0.03)`.
- Default `Z_OPT_INITIAL = c(0.0, 0.0, 0.0, 0.0)`.
- Default `DRIFT_VELOCITY = c(0.3, 0.0, 0.0, 0.0)`.
- Default `DRIFT_END_GEN = 40`.
- Strictly additive genotype-to-breeding-value map, one trait per QTL.
- Moving optimum logged to a separate optimum CSV.
- Full breeding-value cloud logged each generation.

The diagnostic source `compute_diagnostics.py` also matches the Appendix S5 calculations:

- Auto-detects any number of trait columns `a1..aN`.
- Reads a time-varying optimum CSV.
- Computes empirical `G`, sorted eigenvalues of `G`, `mu_i` eigenvalues of `Gamma G`, analytical gradient `b`, `V_lin`, `V_quad`, `A_g`, and empirical `R^2`.
- Prints the identity check `max |2*V_quad - sum(mu_i^2)|`.

The one-replicate driver `run_n_traits.sh` correctly runs the four-trait moving-optimum scenario for replicate 1.

### Existing output verified

I recomputed diagnostics from the included four-trait replicate:

```text
Input BV file:  output/rep_01_4trait_moving_bv.csv
Input optimum:  output/rep_01_4trait_moving_opt.csv
Rows:           400,000 = 200 generations x 2,000 individuals
Traits:         4
Output rows:    200 diagnostic rows
```

The recomputed diagnostics matched the existing `rep_01_4trait_moving_diag.csv` to numerical precision. The most important checks were:

```text
median |A_g - R^2| across generations: 0.0131236909
max |2*V_quad - sum(mu_i^2)|:          2.91e-16
```

The single-replicate summary agrees with the manuscript's reported median absolute difference of about `0.013`, but of course this is not the full 20-replicate check.

## What is missing from the uploaded ZIP

### 1. The 20-replicate production driver is missing

The uploaded `run_n_traits.sh` runs only `rep_01_4trait_moving` with seed `42`. Appendix S5 claims 20 replicates with seeds `42..61`. The code needs a loop driver.

### 2. The Appendix S5 figure-generation script is missing

The uploaded plotting scripts generate single-replicate proof-of-concept figures:

- `plot_trajectory.py` -> `poc_rep_01_4trait_moving.png`
- `plot_geometry.py` -> `geometry_rep_01_4trait_moving.png`

They do not generate the three exact figure files included in the manuscript:

- `multiseed_4trait_moving.png`
- `cv_4trait_moving.png`
- `geom_invariants_4trait_moving.png`

### 3. Only one four-trait replicate is present

The uploaded output folder contains only:

- `rep_01_4trait_moving_bv.csv`
- `rep_01_4trait_moving_opt.csv`
- `rep_01_4trait_moving_diag.csv`

For full Appendix S5 reproducibility, the repository or external archive needs either:

- all 20 per-replicate BV/optimum/diagnostic outputs, or
- a clear script that regenerates them from the SLiM source.

The safer option is both: include the regeneration script in the repository and deposit the large per-replicate outputs in an archive if the repository becomes too heavy.

### 4. Version/citation issue: code says SLiM 5.2, manuscript cites SLiM 3

The manuscript currently cites Haller & Messer 2019, the SLiM 3 paper. The uploaded scripts explicitly require SLiM 5.2 and use SLiM 5 terminology such as `haplosomes`. This is not necessarily wrong, but it should be made internally consistent before submission.

Recommended fix:

- Keep the manuscript wording as "SLiM" rather than "SLiM 3" unless the exact version is specified.
- In Data/Code availability or Appendix S5, state: "Simulations were run in SLiM 5.2 or later."
- Verify and add the correct SLiM 5 citation if available; otherwise cite the accepted official release paper appropriate to the installed SLiM version used.

### 5. Repository hygiene

The uploaded zip includes `.venv/`, `__MACOSX/`, and `.DS_Store` artefacts. These should not go into GitHub or Zenodo source deposits. Suggested `.gitignore` entries:

```gitignore
.venv/
__MACOSX/
.DS_Store
*.pyc
__pycache__/
```

## Reproduction patch prepared

I prepared three add-on files:

- `run_20_reps_appendix_s5.sh`
- `make_appendix_s5_figures.py`
- `README_supplement_reproduction.md`

Copy them into the root of `slim_validation/`, then run:

```bash
cd slim_validation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
chmod +x run_20_reps_appendix_s5.sh
./run_20_reps_appendix_s5.sh
```

The script will run seeds `42..61`, compute diagnostics for each replicate, and write:

```text
figures/multiseed_4trait_moving.png
figures/cv_4trait_moving.png
figures/geom_invariants_4trait_moving.png
output/appendix_s5_summary.csv
```

I tested the aggregation/figure script on the one included replicate. It successfully generated all three manuscript-named figure files structurally, but with only one replicate the CV panels are not biologically meaningful because across-replicate variance requires at least two replicates and Appendix S5 specifically requires 20.

## Final assessment

The attached SLiM work is **close, but not yet complete** for the supplement as written.

It can support Appendix S5 once the 20-replicate driver and multi-seed figure builder are added. The simulation source and diagnostic calculations are consistent with the design described in the manuscript, and the included replicate passes the numerical identity check. The current uploaded zip, by itself, does not yet reproduce the Appendix S5 figures or the 20-replicate claims because it only contains a single replicate and lacks the aggregation layer.

