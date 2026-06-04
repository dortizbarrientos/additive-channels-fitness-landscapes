# Appendix S5 SLiM validation: reproducible figures

This directory contains the reproducible SLiM and Python pipeline for Appendix S5 of
*Additive Channels in Curved Fitness Landscapes*.

The default pipeline runs the four-trait moving-optimum validation described in the manuscript:
20 stochastic SLiM replicates, seeds `42..61`, fixed population size `N = 2000`, 200 QTLs
across four traits, a strictly additive genotype-to-breeding-value map, Gaussian stabilising
selection, and a moving optimum on trait 1 that freezes after generation 40.

## One-command reproduction

From this directory, run:

```bash
chmod +x run_all.sh
./run_all.sh
```

The script creates or reuses a local Python virtual environment, installs `numpy`, `pandas`,
and `matplotlib`, runs the SLiM replicates, computes diagnostics, and builds the Appendix S5
figures.

SLiM must already be installed and available on the command line. Check this with:

```bash
which slim
slim -v
```

If the SLiM executable has a different name or location, run for example:

```bash
SLIM=/Applications/SLiM.app/Contents/MacOS/slim ./run_all.sh
```

You can also use `SLIM_BIN=/path/to/slim`.

## Expected outputs

After a successful full run, the publication-style outputs are:

```text
figures/multiseed_4trait_moving.png
figures/multiseed_4trait_moving.pdf
figures/cv_4trait_moving.png
figures/cv_4trait_moving.pdf
figures/geom_invariants_4trait_moving.png
figures/geom_invariants_4trait_moving.pdf
output/appendix_s5_summary.csv
logs/run_all_environment.txt
logs/run_all_manifest.txt
```

The PNG files are convenient for quick inspection; the PDF files are suitable for manuscript or
archival use. The summary CSV records the numerical checks used in the appendix, including
`median_abs_Ag_minus_R2_all` and `max_abs_2Vquad_minus_sum_mu2`.

## Useful script options

```bash
./run_all.sh --clean          # remove previous Appendix S5 outputs before running
./run_all.sh --resume         # skip replicates whose diagnostic CSV already exists
./run_all.sh --skip-slim      # rebuild figures from existing output/*_diag.csv files
./run_all.sh --figures-only   # alias for --skip-slim
./run_all.sh --quick          # two-replicate smoke test; not the manuscript result
./run_all.sh --reps 5         # short non-manuscript run
./run_all.sh --seed-start 100 # start seeds at 100 rather than 42
./run_all.sh --no-venv        # use the currently active Python/Conda environment
./run_all.sh --help           # show all options
```

Use the default 20-replicate run for the manuscript result. The short-run options are only for
checking that the installation works.

## Main files

```text
run_all.sh                    one-command reproduction driver
slim_sim_n_traits.slim         SLiM forward-time simulation
compute_diagnostics.py         computes G, b, Vlin, Vquad, Ag, empirical R2, eigen checks
make_appendix_s5_figures.py    aggregates replicates and builds Figures S5.1--S5.3
requirements.txt               Python dependencies
SIMULATION_DESIGN.md           detailed design notes
```

## Outputs not tracked by git

The script writes generated data, figures, logs, and the optional local environment to:

```text
output/
figures/
logs/
.venv/
```

These can be omitted from the source repository if the generated CSVs and figures are archived
separately. If the journal asks for per-replicate files, archive `output/rep_*_4trait_moving_*.csv`
alongside the source scripts.

## Fast reproduction

For one-command reproduction of the Appendix S5 validation, use the parallel driver:

```bash
chmod +x run_all.sh
./run_all.sh --clean --jobs auto
```

On a high-core Apple Silicon workstation, `./run_all.sh --clean --jobs 20` runs the 20 independent manuscript replicates concurrently. See `README_RUN_ALL.md` for details.

