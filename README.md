# Additive Channels in Curved Fitness Landscapes — figure reproduction

Daniel Ortiz-Barrientos and Mark Cooper

This repository reproduces and verifies the figures of the manuscript *Additive
Channels in Curved Fitness Landscapes* (GENETICS). It is a **figure package
only** — it does not contain the manuscript text, submission files, or response
to reviewers.

The central object of the paper is the additivity index

```
A_g = V_lin / (V_lin + V_quad),
```

the fraction of log-fitness variance carried by the locally linear part of a
curved fitness surface. Appendix S5 confirms in forward-time simulation that
this analytical quantity equals the fraction of fitness variance an additive
predictor explains: `A_g = R^2`.

## What this repository claims

| Figures | Claim | Reproduced how |
| --- | --- | --- |
| 1-5 (main text) | curated final | final PDFs verified present and checksummed; generating code archived in `figure_sources/` |
| S5.1-S5.3 (Appendix S5) | reproducible simulation | regenerated from SLiM, or rebuilt from tracked diagnostics, in `slim/` |

The main-text figures are included as their final files; the code that made
Figures 2, 4, and 5 is kept under `figure_sources/` so it can be inspected and
rerun by hand. The Appendix S5 figures are the one fully regenerable component.
See [`FIGURE_PROVENANCE.md`](FIGURE_PROVENANCE.md) for the figure-by-figure map.

## Layout

```text
README.md  LICENSE  MANIFEST_NOTES.md  FIGURE_PROVENANCE.md
requirements.txt  run_all.sh  verify_outputs.py
commands.tsv  figure_manifest.tsv

figures/                 # final figures (5 main + 3 Appendix S5)
figure_sources/
    figure2/  figure4/  figure5/   # generation bundles for Figures 2, 4, 5
slim/                    # Appendix S5 SLiM reproduction bundle
    reproduce_appendix_s5.sh  slim_sim_n_traits.slim
    compute_diagnostics.py  make_appendix_s5_figures.py
    SIMULATION_DESIGN.md  requirements.txt  README.md
    output/              # per-replicate *_diag.csv + appendix_s5_summary.csv (tracked)
```

The directory names under `figure_sources/` follow the manuscript figure
numbers; the script names inside follow the older internal numbering (the source
for Figure 4 is `figure3_trajectory.py`, for Figure 5
`figure4_natural_vs_breeding.py`). This is noted in `FIGURE_PROVENANCE.md`.

## Verify the figures

From a fresh clone:

```bash
git clone https://github.com/dortizbarrientos/additive-channels-fitness-landscapes.git
cd additive-channels-fitness-landscapes
./run_all.sh
```

`run_all.sh` confirms every final figure listed in `commands.tsv` is present and
records its size and SHA-256 to `_repro_logs/output_checksums.tsv`. It needs no
SLiM and no Python packages: it is a verification pass, not a regeneration pass.

To inspect or rerun a main-figure bundle by hand (optional):

```bash
cd figure_sources/figure2
python -m venv .venv && source .venv/bin/activate
pip install -r ../../requirements.txt
python figure2_validation.py
```

## Reproduce the Appendix S5 figures

The bundle in `slim/` reproduces the three S5 figures from a forward-time SLiM
simulation: a diploid population of N = 2000, four traits with 50 QTL each, a
fitness optimum drifting along trait 1 for 40 generations, run for 200
generations across 20 stochastic replicates (seeds 42-61).

```bash
cd slim
./reproduce_appendix_s5.sh              # full run (requires SLiM 5.2)
./reproduce_appendix_s5.sh --skip-slim  # rebuild from tracked diagnostics, no SLiM
./reproduce_appendix_s5.sh -j 20        # parallel: one worker per replicate
```

Because the figures are stochastic and PNG bytes are not reproducible across
platforms, the run asserts the framework's identities rather than figure bytes:
the across-replicate median `|A_g - R^2|` stays near 0.013, and
`2*V_quad = sum(mu_i^2)` holds to numerical precision. The per-replicate
diagnostic CSVs and the summary are tracked, so the figures can be rebuilt
without SLiM; the heavy raw breeding-value dumps are not tracked and are
deposited with the archival release. Simulations were run in SLiM 5.2 (Haller,
Ralph & Messer, *Molecular Biology and Evolution* 43(1):msaf313, 2026). See
`slim/README.md`.

## Manifest files

`commands.tsv` is the verification manifest read by `run_all.sh`: one row per
figure, with the check command, expected output, status, and a note.
`figure_manifest.tsv` is a compact index of figure -> final file -> source.
`verify_outputs.py` records existence, sizes, and SHA-256 checksums.

## Licence

See [`LICENSE`](LICENSE).

## Citation

Please cite the associated manuscript and this repository when using or adapting
the code or figures; a full citation and an archival DOI for the tagged release
(including the full raw simulation outputs) will be added on publication.
