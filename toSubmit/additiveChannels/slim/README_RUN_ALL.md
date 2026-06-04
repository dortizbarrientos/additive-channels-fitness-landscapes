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

It also writes `output/appendix_s5_summary.csv`, `logs/run_all_environment.txt`, and `logs/run_all_manifest.txt`.

Useful alternatives:

```bash
./run_all.sh --quick          # two-replicate smoke test; not the manuscript result
./run_all.sh --skip-slim      # rebuild figures from existing diagnostic CSVs
./run_all.sh --figures-only   # alias for --skip-slim
./run_all.sh --resume         # skip completed replicate diagnostics
./run_all.sh --clean          # remove previous Appendix S5 outputs before running
./run_all.sh --no-venv        # use the current Python environment
SLIM=/path/to/slim ./run_all.sh
```

Required software: SLiM and Python 3. The script creates a local `.venv` and installs `requirements.txt` by default.
