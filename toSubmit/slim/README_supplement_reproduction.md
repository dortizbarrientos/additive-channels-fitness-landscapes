# Appendix S5 reproduction note

The folder now includes a single top-level driver, `run_all.sh`, for reproducing the Appendix S5 SLiM validation figures.

Run from the folder root:

```bash
chmod +x run_all.sh
./run_all.sh
```

For a quick installation check that does not reproduce the manuscript result, use:

```bash
./run_all.sh --quick
```

To rebuild the figures from already generated diagnostic CSV files without rerunning SLiM, use:

```bash
./run_all.sh --skip-slim
```

Expected figure outputs are:

```text
figures/multiseed_4trait_moving.png
figures/multiseed_4trait_moving.pdf
figures/cv_4trait_moving.png
figures/cv_4trait_moving.pdf
figures/geom_invariants_4trait_moving.png
figures/geom_invariants_4trait_moving.pdf
```

The numerical audit is written to `output/appendix_s5_summary.csv`; environment and output manifests are written to `logs/`.
