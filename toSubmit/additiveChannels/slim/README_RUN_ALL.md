# One-command Appendix S5 reproduction

From this directory, run:

```bash
chmod +x run_all.sh
./run_all.sh
```

The default run executes the SLiM four-trait moving-optimum validation for 20 stochastic replicates using seeds `42..61`, computes diagnostics, and writes the Appendix S5 figures:

- `figures/multiseed_4trait_moving.png` and `.pdf`
- `figures/cv_4trait_moving.png` and `.pdf`
- `figures/geom_invariants_4trait_moving.png` and `.pdf`

It also writes `output/appendix_s5_summary.csv`, `logs/run_all_environment.txt`, `logs/run_all_manifest.txt`, and `logs/run_all_parallel_status.tsv`.

## Parallel execution

Replicates are independent, so `run_all.sh` runs them in parallel by default. The default `--jobs auto` detects available CPU cores and leaves two cores free, capped by the number of replicates. On a high-core Apple Silicon workstation, such as an M2 Ultra, the default will usually run almost all 20 manuscript replicates at the same time.

For Daniel's M2 Ultra-style workstation, the most direct full run is:

```bash
./run_all.sh --clean --jobs 20
```

A slightly more conservative run is:

```bash
./run_all.sh --clean --jobs 16
```

If the run is interrupted, resume without rerunning completed diagnostics:

```bash
./run_all.sh --resume --jobs 20
```

## Useful alternatives

```bash
./run_all.sh --quick          # two-replicate smoke test; not the manuscript result
./run_all.sh --skip-slim      # rebuild figures from existing diagnostic CSVs
./run_all.sh --figures-only   # alias for --skip-slim
./run_all.sh --resume         # skip completed replicate diagnostics
./run_all.sh --clean          # remove previous Appendix S5 outputs before running
./run_all.sh --serial         # run one replicate at a time
./run_all.sh --jobs 8         # run eight replicate jobs concurrently
./run_all.sh --no-venv        # use the current Python environment
SLIM=/path/to/slim ./run_all.sh --jobs 20
```

Required software: SLiM and Python 3. The script creates a local `.venv` and installs `requirements.txt` by default.

The script also sets `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `VECLIB_MAXIMUM_THREADS`, and `NUMEXPR_NUM_THREADS` to `1` by default, so parallel replicate jobs do not oversubscribe numerical-library threads during diagnostics. You can override those values before running if needed.
