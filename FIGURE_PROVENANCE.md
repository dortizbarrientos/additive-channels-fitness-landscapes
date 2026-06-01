# Figure provenance

This repository contains the reviewer-facing reproducibility package for:

**Additive Channels in Curved Fitness Landscapes**  
Daniel Ortiz-Barrientos and Mark Cooper

The final manuscript includes five main-text figures and three Appendix S5 simulation/diagnostic outputs. The runner `run_all.sh` reads `commands.tsv`, executes one command per figure, and verifies expected outputs with SHA-256 checksums.

## Figure map

| Manuscript item | Final output | Source/provenance | Status |
|---|---|---|---|
| Figure 1 | `revision/tex/additiveChannels/additiveChannels/figures/figure1_channel.pdf` | Curated final PDF | Final output included; exact editable source not isolated |
| Figure 2 | `revision/tex/additiveChannels/additiveChannels/figures/figure2_validation.pdf` | `revision/figures/figure2/figure2_validation.py` | Reproduced from code |
| Figure 3 | `revision/tex/additiveChannels/additiveChannels/figures/figure3_framework.pdf` | Curated final PDF | Final output included; exact editable source not isolated |
| Figure 4 | `revision/tex/additiveChannels/additiveChannels/figures/figure4_trajectory.pdf` | `revision/figures/figure3/figure3_trajectory.py` | Reproduced from code and renamed |
| Figure 5 | `revision/tex/additiveChannels/additiveChannels/figures/figure5_natural_vs_breeding.pdf` | `revision/figures/figure4/figure4_natural_vs_breeding.py` and `sim_core.py` | Reproduced from code and renamed |
| Appendix S5.1 | `revision/tex/additiveChannels/additiveChannels/figures/multiseed_4trait_moving.png` | Curated final simulation output | Final output included; full generator not isolated |
| Appendix S5.2 | `revision/tex/additiveChannels/additiveChannels/figures/cv_4trait_moving.png` | Curated final simulation output | Final output included; full generator not isolated |
| Appendix S5.3 | `revision/tex/additiveChannels/additiveChannels/figures/geom_invariants_4trait_moving.png` | Curated final simulation output | Final output included; full generator not isolated |

## Notes on figure numbering

During revision, some code bundles retained older internal names. In particular, the code folder `revision/figures/figure3/` generates the final manuscript Figure 4, and the code folder `revision/figures/figure4/` generates the final manuscript Figure 5. The final filenames in the manuscript are produced by copying the generated outputs into the final manuscript figure folder under the manuscript names.

## Reproduction command

Use a virtual environment rather than installing into the system Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
./run_all.sh
```

The script writes logs and checksums to `_repro_logs/`, which is intentionally not tracked by Git.
