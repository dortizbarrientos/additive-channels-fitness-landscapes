# Additive Channels in Curved Fitness Landscapes — figure reproduction

Daniel Ortiz-Barrientos and Mark Cooper

This repository holds the figures of the paper *Additive Channels in Curved
Fitness Landscapes* (GENETICS), the code that produced them, and a runner that
verifies them. It does not contain the manuscript text or the submission files.

The paper's central quantity is the additivity index

```
A_g = V_lin / (V_lin + V_quad),
```

the share of log-fitness variance carried by the linear part of a curved fitness
surface. Appendix S5 shows in simulation that this analytical quantity equals
`R^2`, the share of fitness variance that an additive predictor explains.

## Reproducibility

This repository keeps three levels of reproducibility distinct. Figures 1 and 3
are hand-drawn schematics with no generating script; they are curated final
files, verified present and checksummed. Figures 2, 4, and 5 are computational.
Their final PDFs are curated and verified, and the code that produced them sits
in `figure_sources/`, where a reader can read it or run it by hand. The three
Appendix S5 figures are the only ones the repository regenerates from source:
`slim/` rebuilds them from the SLiM simulation and checks two identities, the
median `|A_g - R^2|` near 0.013 and `2*V_quad = sum(mu_i^2)` to numerical
precision. The run tests those numbers, not the figure pixels.

## Verify the figures

Clone the repository and run the verifier:

```bash
git clone https://github.com/dortizbarrientos/additive-channels-fitness-landscapes.git
cd additive-channels-fitness-landscapes
./run_all.sh
```

`run_all.sh` confirms that every final figure named in `commands.tsv` exists, and
records its size and SHA-256 in `_repro_logs/output_checksums.tsv`. It runs no
simulation and needs no Python packages.

To run a main-figure script by hand, install the dependencies first:

```bash
cd figure_sources/figure2
python -m venv .venv && source .venv/bin/activate
pip install -r ../../requirements.txt
python figure2_validation.py
```

## Reproduce the Appendix S5 figures

The `slim/` folder rebuilds the three Appendix S5 figures from the simulation.
From `slim/`:

```bash
./reproduce_appendix_s5.sh              # full run; requires SLiM 5.2
./reproduce_appendix_s5.sh --skip-slim  # rebuild from the tracked diagnostics; no SLiM
./reproduce_appendix_s5.sh -j 20        # run the replicates in parallel
```

`slim/README.md` describes the model and the checks.

## Layout

```text
README.md  LICENSE  MANIFEST_NOTES.md  FIGURE_PROVENANCE.md
requirements.txt  run_all.sh  verify_outputs.py
commands.tsv  figure_manifest.tsv
figures/            five main figures and three Appendix S5 figures
figure_sources/     generating code for Figures 2, 4, and 5
slim/               Appendix S5 SLiM reproduction
```

The folders under `figure_sources/` carry the manuscript figure numbers; the
scripts inside keep older internal names. The script for Figure 4 is
`figure3_trajectory.py`, and the script for Figure 5 is
`figure4_natural_vs_breeding.py`. `FIGURE_PROVENANCE.md` records this.

## Manifest files

`commands.tsv` lists, for each figure, the check the runner performs, the
expected output, and its status. `figure_manifest.tsv` indexes each figure to its
final file and its source. `verify_outputs.py` records existence, size, and
SHA-256.

## Licence

See `LICENSE`.

## Citation

Cite the paper and this repository when you use or adapt the code or figures. A
full citation and an archival DOI for the data release will follow on
publication. The simulations use SLiM 5.2 (Haller, Ralph, and Messer, *Molecular
Biology and Evolution* 43(1):msaf313, 2026).
