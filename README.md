# Additive channels in curved fitness landscapes

This repository contains the reviewer-facing reproducibility package for the figures associated with:

**Additive Channels in Curved Fitness Landscapes**  
Daniel Ortiz-Barrientos and Mark Cooper

The package is intentionally small. It retains the final manuscript figure files, the code bundles needed to regenerate the code-generated figures, and a manifest-based runner that checks all expected outputs.

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
```

## Quick start

From a fresh clone:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
./run_all.sh
```

The runner reads `commands.tsv`, executes one command per figure item, and writes checksums to `_repro_logs/output_checksums.tsv`.

## Output behaviour

The final manuscript figures are kept under:

```text
revision/tex/additiveChannels/additiveChannels/figures/
```

To avoid making the Git working tree dirty after each run, regenerated code-based figures are written to:

```text
_repro_outputs/
```

This directory is ignored by Git. The runner also checks that the curated final outputs are present.

## Figure provenance

See `FIGURE_PROVENANCE.md` for the figure-by-figure mapping between final manuscript outputs, code-generated outputs, and curated final outputs.
