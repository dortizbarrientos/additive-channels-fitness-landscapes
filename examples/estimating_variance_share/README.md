# From reproductive counts to a variance share

This example accompanies **Supplementary File 3** of *Additive Channels in Curved Fitness Landscapes*. It follows the manuscript's estimation section using one trait, repeated noisy measurements and counts of surviving offspring. The estimator never receives the simulated true breeding values.

Read [the worked example](Supplementary_File_3_Worked_Estimation.pdf), then explore the same calculations in the Shiny for Python app.

## Run from the repository root

```bash
bash run_shiny.sh
```

This creates `.venv-estimation`, installs dependencies on the first run, and opens the local app at `http://127.0.0.1:8000`. Python 3.10 or newer is required. No R installation is needed. Use `SHINY_PORT=8001 bash run_shiny.sh` to choose another port; stop with Ctrl-C. An internet connection is needed for the initial dependency installation. The app runs on your computer and is not a hosted service.

To regenerate the saved dataset, estimates, 500 bootstrap samples and figures:

```bash
bash run_estimation.sh
```

The default output goes to this folder's `results/`. Use `bash run_estimation.sh --output /path/to/new/results` to preserve the archived example. A quick demonstration is `bash run_estimation.sh --bootstrap 20 --output /path/to/demo`; 20 replicates are too few for a stable uncertainty interval. The command regenerates numerical results and figures, not the typeset tutorial. With TeX Live or MacTeX installed, compile the tutorial from this example directory using `latexmk -pdf Supplementary_File_3_Worked_Estimation.tex`.

## The five steps

1. Define one population and reproductive episode: 800 unrelated genotypes, three height measurements each and one offspring count.
2. Estimate genetic and environmental variance from the repeated measurements. Fit the count likelihood while integrating over uncertain breeding values.
3. Differentiate the quadratic log mean at the estimated population mean to obtain slope `b` and curvature `H`.
4. Calculate `V_lin = b²G`, `V_quad = H²G²/2` and `A_g = V_lin/(V_lin + V_quad)`.
5. Resimulate and refit both stages for uncertainty; compare observable predictions with data and examine a higher-order alternative.

For seed 20261005, the generating share is **0.6667**, the estimate is **0.6107**, and the 95% parametric bootstrap interval is **0.5330–0.6857**. The interval is conditional on the quadratic observation model; it does not cover model misspecification. All 500 default bootstrap fits completed without reaching parameter bounds. Numerical integration is checked at increasing orders, including in bootstrap fits. Unresolved integrals or nonpositive estimated genetic variance produce an explicit failure.

The app combines steps 3–4 in one tab and divides step 5 into uncertainty and model checks. Changing a setting does not change the displayed analysis until **Generate and estimate** is pressed. A new dataset clears old intervals. Downloads contain the displayed observations, truth, settings, estimates and any completed bootstrap samples.

## Assumptions and interpretation

The trait is wholly additive by construction. Independent clonal measurements identify additive variance only under this assumption: dominance, epistasis, permanent environments and a shared measurement/reproductive environment are absent. Related or genomic data require a suitable relationship model. This is a transparent two-stage teaching estimator, not a general animal-model implementation.

The target is variance in **log expected reproductive output across breeding values**, not variance in observed offspring counts or accuracy of evolutionary response. Zeros are retained in a Poisson likelihood and never logged. The intercept gives expected output at the population mean, not the population mean of output.

The naive comparator treats predicted breeding values as exact and substitutes their shrunken variance for `G`. It re-estimates the slope and curvature, so its error has no universal direction. The fourth-order option keeps the generating local slope and curvature fixed while changing the fitness relationship away from the mean. The app distinguishes the local quadratic share from the affine R² of that complete relationship. The quadratic bootstrap is not a correction for this mismatch.

## Files

| File | Purpose |
|---|---|
| `model.py` | Simulation, measurement calibration, integrated likelihood, bootstrap and known values |
| `plots.py` | Shared plots for the tutorial and app |
| `run_case.py` | Reproduce the saved numerical case and figures |
| `app.py` | Shiny user interface calling the same model functions |
| `test_model.py` | Independent numerical and simulation checks |
| `Supplementary_File_3_Worked_Estimation.tex` | Standalone tutorial source; requires the tables and figures in `results/` |
| `results/observed_data.csv` | `id`, `offspring` count, and `height_1`–`height_3` deviations in cm |
| `results/simulation_truth.csv` | Hidden `true_breeding_value` in cm, matched by `id`; never an estimator input |
| `results/estimates.csv` | Generating values, estimates, intervals and naive comparison |
| `results/bootstrap_draws.csv` | Each successful refit, including genetic and environmental variance |
| `results/summary.json` | Parameters, results, failure/boundary counts, quadrature check, versions and data checksum |

After either launch command has installed the environment, run checks from the repository root with:

```bash
.venv-estimation/bin/python -m unittest discover -s examples/estimating_variance_share -p 'test_*.py' -v
```

These compare Gaussian moments, the expected count with a closed-form integral, the integrated likelihood with independent adaptive integration, the nearly observed-breeding-value limit, repeated-simulation recovery, bootstrap recalibration and the fourth-order variance formula. This static estimation example is separate from the repository's multigeneration SLiM simulations.
