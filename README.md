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
````

The folders `revision/figures/figure3/` and `revision/figures/figure4/` retain their older internal names from the revision history. In the final manuscript, these correspond to Figure 4 and Figure 5, respectively. This mapping is made explicit in `commands.tsv`, `figure_manifest.tsv`, and `FIGURE_PROVENANCE.md`. The directory name `revision/` is retained from the manuscript revision history. In this minimal repository it contains only the retained figure-generation bundles and final manuscript figure outputs used by the reproducibility runner.

## Quick start

From a fresh clone:

```bash
git clone https://github.com/dortizbarrientos/additive-channels-fitness-landscapes.git
cd additive-channels-fitness-landscapes

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

./run_all.sh
```

A successful run writes logs and checksums to:

```text
_repro_logs/output_checksums.tsv
```

and writes regenerated code-based figures to:

```text
_repro_outputs/
```

Both folders are local run products and are ignored by Git.

## Expected output behaviour

The final manuscript figures are tracked under:

```text
revision/tex/additiveChannels/additiveChannels/figures/
```

The runner does not overwrite the tracked final manuscript PDFs for the code-generated figures. Instead, it regenerates those figures into `_repro_outputs/` and verifies the expected outputs listed in `commands.tsv`. This keeps the working tree clean after a successful run and avoids unnecessary PDF checksum changes caused by metadata, font embedding, or save-time differences.

After running:

```bash
./run_all.sh
git status --short
```

`git status --short` should not report modified tracked figure files. Local folders such as `.venv/`, `_repro_logs/`, `_repro_work/`, and `_repro_outputs/` are expected and ignored.

## Figure map

| Manuscript item | Final manuscript output                                                                    | Code-generated or checked output                 | Provenance status                                                                                                      |
| --------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| Figure 1        | `revision/tex/additiveChannels/additiveChannels/figures/figure1_channel.pdf`               | checked in place                                 | curated final output                                                                                                   |
| Figure 2        | `revision/tex/additiveChannels/additiveChannels/figures/figure2_validation.pdf`            | `_repro_outputs/figure2_validation.pdf`          | regenerated from `revision/figures/figure2/figure2_validation.py`                                                      |
| Figure 3        | `revision/tex/additiveChannels/additiveChannels/figures/figure3_framework.pdf`             | checked in place                                 | curated final output                                                                                                   |
| Figure 4        | `revision/tex/additiveChannels/additiveChannels/figures/figure4_trajectory.pdf`            | `_repro_outputs/figure4_trajectory.pdf`          | regenerated from `revision/figures/figure3/figure3_trajectory.py` and written under the final manuscript name          |
| Figure 5        | `revision/tex/additiveChannels/additiveChannels/figures/figure5_natural_vs_breeding.pdf`   | `_repro_outputs/figure5_natural_vs_breeding.pdf` | regenerated from `revision/figures/figure4/figure4_natural_vs_breeding.py` and written under the final manuscript name |
| Appendix S5.1   | `revision/tex/additiveChannels/additiveChannels/figures/multiseed_4trait_moving.png`       | checked in place                                 | curated final simulation output                                                                                        |
| Appendix S5.2   | `revision/tex/additiveChannels/additiveChannels/figures/cv_4trait_moving.png`              | checked in place                                 | curated final simulation output                                                                                        |
| Appendix S5.3   | `revision/tex/additiveChannels/additiveChannels/figures/geom_invariants_4trait_moving.png` | checked in place                                 | curated final simulation output                                                                                        |

## Manifest files

`commands.tsv` is the execution manifest read by `run_all.sh`. Each row contains one figure item, one shell command, the expected output path, the provenance status, and a short note.

`figure_manifest.tsv` is a compact figure index linking manuscript figure labels to final output paths and provenance status.

`FIGURE_PROVENANCE.md` gives the more detailed explanation of how each final manuscript output relates to the retained source code or curated final output.

`verify_outputs.py` checks that the expected outputs exist and records file sizes and SHA-256 checksums.

## Troubleshooting

If macOS or Homebrew reports an “externally managed environment” error during installation, use the virtual-environment commands above rather than installing packages into the system Python.

If the runner is not executable, run:

```bash
chmod +x run_all.sh verify_outputs.py
```

If a successful run leaves tracked PDFs marked as modified, check that `commands.tsv` writes regenerated outputs to `_repro_outputs/` rather than directly into the tracked manuscript figure folder. To restore tracked manuscript figures to the committed versions, use:

```bash
git restore revision/tex/additiveChannels/additiveChannels/figures/figure2_validation.pdf \
            revision/tex/additiveChannels/additiveChannels/figures/figure4_trajectory.pdf \
            revision/tex/additiveChannels/additiveChannels/figures/figure5_natural_vs_breeding.pdf
```

## Licence

See [`LICENSE`](LICENSE) for the licence terms.

## Citation

Please cite the associated manuscript and this repository when using or adapting the code or figures. A full citation can be added here after publication.
