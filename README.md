# Additive channels in curved fitness landscapes

**Additive Channels in Curved Fitness Landscapes**  
Daniel Ortiz-Barrientos and Mark Cooper

## Contents

The repository keeps only the files needed to inspect the manuscript figures and reproduce the code-generated outputs.

```text
README.md
MANIFEST_NOTES.md
requirements.txt
run_all.sh
verify_outputs.py
commands.tsv
figure_manifest.tsv
FIGURE_PROVENANCE.md

revision/figures/figure2/
revision/figures/figure3/
revision/figures/figure4/

revision/tex/additiveChannels/additiveChannels/figures/

toSubmit/main_paper_with_page_lines.tex
toSubmit/main_paper_with_page_lines.pdf
```

## Quick start

Use a virtual environment rather than installing into the system Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
./run_all.sh
```

The script reads `commands.tsv`, runs each figure command, and verifies the expected outputs by writing checksums to `_repro_logs/output_checksums.tsv`.

## Provenance

See `FIGURE_PROVENANCE.md` for the figure-by-figure mapping between final manuscript outputs and the code or curated source files used to produce them.
