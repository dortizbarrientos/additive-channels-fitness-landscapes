# Manifest notes

The repository is organised as a minimal reproducibility package for the GENETICS/Additive Channels manuscript figures.

`commands.tsv` is the executable manifest used by `run_all.sh`. Each row gives a figure identifier, the command used to reproduce or verify the output, the expected output path, a status tag, and a short note.

`figure_manifest.tsv` is a compact human-readable map from manuscript figure items to final outputs and source/provenance notes.

`FIGURE_PROVENANCE.md` gives the longer figure-by-figure explanation, including the older internal numbering retained by some source-code folders.

The directories `_repro_work/`, `_repro_outputs/`, and `_repro_logs/` are created during local reproduction and are intentionally ignored by Git.
