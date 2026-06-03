# Additive channels in curved fitness landscapes

**Additive Channels in Curved Fitness Landscapes**  
Daniel Ortiz-Barrientos and Mark Cooper

This repository is a lightweight reproducibility package that includes final figures, the code used to generate them, and a runner to verify the results.

## Reproducibility scope

The package supports two levels of reproducibility.

First, it regenerates the figures whose final code bundles are included in this repository: final Figure 2, final Figure 4, and final Figure 5. These regenerated files are written to `_repro_outputs/` so that a successful run does not overwrite the tracked manuscript figures.

Second, it verifies that all final manuscript figure files are present and records their checksums. This includes the curated schematic outputs and the Appendix S5 simulation/diagnostic outputs for which the final figure files are retained.

For the figure-by-figure mapping, see [`FIGURE_PROVENANCE.md`](FIGURE_PROVENANCE.md).

## Repository contents

```text
README.md
MANIFEST_NOTES.md
FIGURE_PROVENANCE.md
LICENSE
requirements.txt
run_all.sh
verify_outputs.py
commands.tsv
figure_manifest.tsv

revision/figures/figure2/       # source bundle for final Figure 2
revision/figures/figure3/       # source bundle for final Figure 4; old internal name retained
revision/figures/figure4/       # source bundle for final Figure 5; old internal name retained

revision/tex/additiveChannels/additiveChannels/figures/
    figure1_channel.pdf
    figure2_validation.pdf
    figure3_framework.pdf
    figure4_trajectory.pdf
    figure5_natural_vs_breeding.pdf
    multiseed_4trait_moving.png
    cv_4trait_moving.png
    geom_invariants_4trait_moving.png

toSubmit/main_paper_with_page_lines.tex
toSubmit/main_paper_with_page_lines.pdf
