# Figure provenance

This repository reproduces and verifies the figures of *Additive Channels in
Curved Fitness Landscapes*. It makes two kinds of claim.

- **Curated final** — the figure is included as its final file; the code that
  generated it is archived alongside (under `figure_sources/`) so it can be
  inspected and rerun by hand, but the runner only verifies the final file is
  present and records its checksum.
- **Reproducible simulation** — the figure is regenerated from source by the
  SLiM bundle in `slim/`.

| Figure | Final file | Source | Claim |
| --- | --- | --- | --- |
| 1 | `figures/figure1_channel.pdf` | curated final PDF | curated final |
| 2 | `figures/figure2_validation.pdf` | `figure_sources/figure2/figure2_validation.py` | curated final |
| 3 | `figures/figure3_framework.pdf` | curated final PDF | curated final |
| 4 | `figures/figure4_trajectory.pdf` | `figure_sources/figure4/figure3_trajectory.py` | curated final |
| 5 | `figures/figure5_natural_vs_breeding.pdf` | `figure_sources/figure5/figure4_natural_vs_breeding.py` | curated final |
| S5.1 | `figures/multiseed_4trait_moving.png` | `slim/` (SLiM 5.2) | reproducible simulation |
| S5.2 | `figures/cv_4trait_moving.png` | `slim/` (SLiM 5.2) | reproducible simulation |
| S5.3 | `figures/geom_invariants_4trait_moving.png` | `slim/` (SLiM 5.2) | reproducible simulation |

## A note on the source filenames for Figures 4 and 5

The generation bundles retain their older internal names from the revision
history: the source for **Figure 4** is `figure3_trajectory.py` (in
`figure_sources/figure4/`), and the source for **Figure 5** is
`figure4_natural_vs_breeding.py` (in `figure_sources/figure5/`). The directory
names follow the **manuscript** figure numbers; the script names inside follow
the older internal numbering. This is the only place the two numbering schemes
meet.

## Reproducing the Appendix S5 figures

The three S5 figures are regenerated from the SLiM simulation and its
per-replicate diagnostics. See `slim/README.md`. In brief, from `slim/`:

```bash
./reproduce_appendix_s5.sh              # full run (requires SLiM 5.2)
./reproduce_appendix_s5.sh --skip-slim  # rebuild from the tracked diagnostic CSVs, no SLiM
```

The run asserts the framework's identities — the across-replicate median
|A_g - R^2| stays near 0.013, and 2*V_quad = sum(mu_i^2) holds to numerical
precision — rather than testing figure bytes, which are not reproducible across
platforms for stochastic output.
