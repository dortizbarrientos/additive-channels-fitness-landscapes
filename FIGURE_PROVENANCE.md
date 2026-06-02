# Figure provenance

This repository contains the reviewer-facing reproducibility package for the figure outputs associated with:

**Additive Channels in Curved Fitness Landscapes**  
Daniel Ortiz-Barrientos and Mark Cooper

The final manuscript includes five main-text figures and three Appendix S5 simulation/diagnostic outputs. The runner `run_all.sh` reads `commands.tsv`, executes one command per figure item, and verifies the expected outputs with SHA-256 checksums.

## Figure map

| Manuscript item | Final manuscript output | Reproduced/check output | Source/provenance | Status |
|---|---|---|---|---|
| Figure 1 | `revision/tex/additiveChannels/additiveChannels/figures/figure1_channel.pdf` | same final file checked for presence | Curated final PDF | Final output included; exact editable source not isolated |
| Figure 2 | `revision/tex/additiveChannels/additiveChannels/figures/figure2_validation.pdf` | `_repro_outputs/figure2_validation.pdf` | `revision/figures/figure2/figure2_validation.py` | Reproduced from code |
| Figure 3 | `revision/tex/additiveChannels/additiveChannels/figures/figure3_framework.pdf` | same final file checked for presence | Curated final PDF | Final output included; exact editable source not isolated |
| Figure 4 | `revision/tex/additiveChannels/additiveChannels/figures/figure4_trajectory.pdf` | `_repro_outputs/figure4_trajectory.pdf` | `revision/figures/figure3/figure3_trajectory.py` | Reproduced from code and renamed |
| Figure 5 | `revision/tex/additiveChannels/additiveChannels/figures/figure5_natural_vs_breeding.pdf` | `_repro_outputs/figure5_natural_vs_breeding.pdf` | `revision/figures/figure4/figure4_natural_vs_breeding.py` and `sim_core.py` | Reproduced from code and renamed |
| Appendix S5.1 | `revision/tex/additiveChannels/additiveChannels/figures/multiseed_4trait_moving.png` | same final file checked for presence | Curated final simulation output | Final output included; full generator not isolated |
| Appendix S5.2 | `revision/tex/additiveChannels/additiveChannels/figures/cv_4trait_moving.png` | same final file checked for presence | Curated final simulation output | Final output included; full generator not isolated |
| Appendix S5.3 | `revision/tex/additiveChannels/additiveChannels/figures/geom_invariants_4trait_moving.png` | same final file checked for presence | Curated final simulation output | Final output included; full generator not isolated |

## Notes on figure numbering

During revision, some code bundles retained older internal names. In particular, the folder `revision/figures/figure3/` generates the final manuscript Figure 4, and the folder `revision/figures/figure4/` generates the final manuscript Figure 5. The runner writes these regenerated outputs to `_repro_outputs/` using the final manuscript names.

## Reproduction command

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
./run_all.sh
```

The script writes logs and checksums to `_repro_logs/`, which is intentionally not tracked by Git.
