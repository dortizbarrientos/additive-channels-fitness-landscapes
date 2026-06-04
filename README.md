# Additive Channels in Curved Fitness Landscapes

Daniel Ortiz-Barrientos and Mark Cooper

Reproducibility package for the manuscript *Additive Channels in Curved Fitness
Landscapes* (GENETICS). It contains the final manuscript figures, the code that
generates them, the SLiM validation behind Appendix S5, and a single runner that
reproduces and verifies the results.

The central object of the paper is the **additivity index**

```
A_g = V_lin / (V_lin + V_quad),
```

the fraction of log-fitness variance carried by the locally linear part of a
curved fitness surface. Appendix S5 confirms, in forward-time simulation, that
this analytical quantity equals the empirical fraction of fitness variance an
additive predictor explains: `A_g = R^2`.

---

## Reproducibility at three levels

| Tier | What it covers | How it is reproduced | Needs SLiM? |
| --- | --- | --- | --- |
| 1. Code-generated figures | Figures 2, 4, 5 | regenerated from Python into `_repro_outputs/` | no |
| 2. Curated figures | Figures 1, 3 | verified present, checksummed in place | no |
| 3. Appendix S5 validation | `multiseed`, `cv`, `geom_invariants` | regenerated from SLiM, or rebuilt from tracked diagnostics | optional |

Tiers 1 and 2 run from the repository root. Tier 3 lives in a self-contained
bundle under `toSubmit/additiveChannels/slim/` and can be reproduced two ways:
fully from SLiM, or — without installing SLiM — from the per-replicate
diagnostic files that are tracked in this repository.

For the figure-by-figure mapping see
[`FIGURE_PROVENANCE.md`](FIGURE_PROVENANCE.md).

---

## Quick start

```bash
git clone https://github.com/dortizbarrientos/additive-channels-fitness-landscapes.git
cd additive-channels-fitness-landscapes

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

./run_all.sh
```

`./run_all.sh` regenerates the code-based main figures, verifies that every
final figure file is present, and writes a checksum log. It does **not** require
SLiM, and it does not overwrite the tracked manuscript figures: regenerated
files go to `_repro_outputs/`, and a checksum log to
`_repro_logs/output_checksums.tsv`.

To also reproduce the Appendix S5 simulation (requires SLiM, see below):

```bash
./run_all.sh --with-sim
```

After any run, the working tree should stay clean:

```bash
./run_all.sh
git status --short        # should report no modified tracked figures
```

Local folders `.venv/`, `_repro_logs/`, `_repro_work/`, and `_repro_outputs/`
are run products and are ignored by Git.

---

## Appendix S5: the SLiM validation

The bundle at `toSubmit/additiveChannels/slim/` reproduces the three Appendix S5
figures and the numerical summary they rest on. The model is a forward-time,
individual-based SLiM simulation: a diploid population of `N = 2000`, four traits
with 50 QTL each (200 QTL total), under a fitness optimum that drifts along
trait 1 for 40 generations and then holds, run for 200 generations across **20
stochastic replicates** with seeds `42..61`. Each replicate's per-generation
diagnostics record `V_lin`, `V_quad`, `A_g`, the empirical `R^2`, and the
eigenvalue structure of **G** and of **ΓG**.

### Running it

```bash
cd toSubmit/additiveChannels/slim

# Full reproduction from SLiM (auto-detects cores; see Parallelism).
./reproduce_appendix_s5.sh

# SLiM-free: rebuild the figures and summary from the tracked diagnostic CSVs.
./reproduce_appendix_s5.sh --skip-slim

# Fast smoke test: two replicates only (not the manuscript result).
./reproduce_appendix_s5.sh --clean --quick
```

The driver writes its figures to `slim/figures/` and its summary to
`slim/output/appendix_s5_summary.csv`. The curated manuscript copies of the S5
figures are tracked separately and are not overwritten.

### What "reproduced" means here

The figures are stochastic SLiM output, and PNG/PDF bytes are not reproducible
across library versions or platforms — so byte-equality is the wrong test.
Instead, the driver asserts the two identities the appendix actually claims:

- the across-replicate median `|A_g − R^2|` stays near the reported value
  (≈ 0.013), and
- the algebraic identity `2·V_quad = Σ μ_i²` holds to numerical precision.

A run that violates either is reported as a failure rather than silently
producing a misleading figure.

### Parallelism

The replicate phase is embarrassingly parallel: each replicate is an independent
SLiM process with a fixed seed, so results are identical for any number of
workers. The driver runs them through a pool.

```bash
./reproduce_appendix_s5.sh -j 20      # 20 workers
JOBS=16 ./reproduce_appendix_s5.sh    # same, via environment
```

By default the driver uses `cores − 2` workers, capped at the replicate count.
Each worker is pinned to a single math thread (`VECLIB_MAXIMUM_THREADS=1` and
the BLAS/OpenMP equivalents) to prevent oversubscription when many replicates
run at once.

### Software

Simulations were run in **SLiM 5.2** (Haller, Ralph & Messer 2026; see
[messerlab.org/slim](https://messerlab.org/slim)). The diagnostic and figure
scripts require Python 3 with `numpy`, `pandas`, and `matplotlib`
(`slim/requirements.txt`). The simulation design is documented in
`slim/SIMULATION_DESIGN.md`.

### Data policy

The per-replicate **diagnostic** CSVs (`output/rep_*_diag.csv`) and the summary
(`output/appendix_s5_summary.csv`) are tracked, so the figures can be rebuilt
without SLiM. The heavy raw breeding-value and optimum dumps
(`output/rep_*_bv.csv`, `output/rep_*_opt.csv`), along with `logs/` and
`figures/`, are regenerable and are not tracked; the full raw set is deposited
in the archival release (see Citation).

---

## Figure map

| Manuscript item | Tracked final output | Reproduced / checked output | Provenance |
| --- | --- | --- | --- |
| Figure 1 | `revision/tex/.../figures/figure1_channel.pdf` | checked in place | curated final |
| Figure 2 | `revision/tex/.../figures/figure2_validation.pdf` | `_repro_outputs/figure2_validation.pdf` | from `revision/figures/figure2/figure2_validation.py` |
| Figure 3 | `revision/tex/.../figures/figure3_framework.pdf` | checked in place | curated final |
| Figure 4 | `revision/tex/.../figures/figure4_trajectory.pdf` | `_repro_outputs/figure4_trajectory.pdf` | from `revision/figures/figure3/figure3_trajectory.py` |
| Figure 5 | `revision/tex/.../figures/figure5_natural_vs_breeding.pdf` | `_repro_outputs/figure5_natural_vs_breeding.pdf` | from `revision/figures/figure4/figure4_natural_vs_breeding.py` |
| Appendix S5.1 | `revision/tex/.../figures/multiseed_4trait_moving.png` | `slim/figures/multiseed_4trait_moving.png` | SLiM (Tier 3); curated PNG tracked |
| Appendix S5.2 | `revision/tex/.../figures/cv_4trait_moving.png` | `slim/figures/cv_4trait_moving.png` | SLiM (Tier 3); curated PNG tracked |
| Appendix S5.3 | `revision/tex/.../figures/geom_invariants_4trait_moving.png` | `slim/figures/geom_invariants_4trait_moving.png` | SLiM (Tier 3); curated PNG tracked |

Paths above abbreviate `revision/tex/additiveChannels/additiveChannels/figures/`.
The directories `revision/figures/figure3/` and `figure4/` retain their older
internal names; in the final manuscript they correspond to Figures 4 and 5. This
mapping is explicit in `commands.tsv`, `figure_manifest.tsv`, and
`FIGURE_PROVENANCE.md`.

---

## Repository layout

```text
run_all.sh                     # top-level runner (Tiers 1–2; --with-sim adds Tier 3)
verify_outputs.py              # existence + SHA-256 checksum verifier
commands.tsv                   # execution manifest read by run_all.sh
figure_manifest.tsv            # compact figure index
FIGURE_PROVENANCE.md           # detailed figure-by-figure provenance
MANIFEST_NOTES.md  LICENSE  requirements.txt

revision/figures/figure2|3|4/  # source bundles for Figures 2, 4, 5
revision/tex/.../figures/      # tracked final manuscript figures (all 5 + 3 S5 PNGs)

toSubmit/additiveChannels/
    text/                      # manuscript .tex/.pdf, references, response to reviewers
    figures/  tables/          # submission figures and data tables
    slim/                      # Appendix S5 SLiM validation bundle (Tier 3)
        reproduce_appendix_s5.sh   # the S5 reproduction driver
        slim_sim_n_traits.slim     # SLiM 5.2 source
        compute_diagnostics.py     # per-replicate diagnostics
        make_appendix_s5_figures.py# aggregation + figures + summary
        SIMULATION_DESIGN.md  requirements.txt  README.md
        output/                    # *_diag.csv + summary tracked; *_bv/_opt ignored
```

---

## Manifest files

`commands.tsv` is the execution manifest: one row per figure item, with the
shell command, expected output path, provenance status, and a note.
`figure_manifest.tsv` is a compact index linking figure labels to output paths.
`verify_outputs.py` checks that expected outputs exist and records sizes and
SHA-256 checksums. `FIGURE_PROVENANCE.md` gives the long-form provenance.

---

## Troubleshooting

If `pip` reports an "externally managed environment" error, use the
virtual-environment commands in Quick start rather than the system Python.

If a runner is not executable:

```bash
chmod +x run_all.sh verify_outputs.py
chmod +x toSubmit/additiveChannels/slim/reproduce_appendix_s5.sh
```

If `./run_all.sh --with-sim` reports that SLiM is not found, install SLiM ≥ 5.2
and ensure `slim` is on your `PATH`, or point the driver at it with
`SLIM_BIN=/path/to/slim`.

If a successful run leaves tracked PDFs marked modified, confirm `commands.tsv`
writes regenerated outputs to `_repro_outputs/` rather than into the tracked
figure folder. To restore tracked figures to their committed versions:

```bash
git restore revision/tex/additiveChannels/additiveChannels/figures/figure2_validation.pdf \
            revision/tex/additiveChannels/additiveChannels/figures/figure4_trajectory.pdf \
            revision/tex/additiveChannels/additiveChannels/figures/figure5_natural_vs_breeding.pdf
```

---

## Licence

See [`LICENSE`](LICENSE).

---

## Citation

Please cite the associated manuscript and this repository when using or adapting
the code or figures; a full citation will be added on publication, with an
archival DOI for the tagged release (and the full raw simulation outputs)
deposited at that time. The simulations use SLiM 5.2 (Haller, Ralph & Messer,
*Molecular Biology and Evolution* 43(1):msaf313, 2026).
