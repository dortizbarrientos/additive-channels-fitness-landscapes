# Additive Channels figure reproducibility audit — v3

This package replaces the earlier audit scripts. It is tailored to the current `5_geneticsS1` tree, where several papers and figure/code histories live together.

The v3 audit does three extra things that matter for this repository:

1. It uses smart scan roots rather than crawling the entire OneDrive tree.
2. It inspects zip archives without extracting them, so files inside `figure2.zip`, `figure3.zip`, `figure4.zip`, and final-verification packages can be detected.
3. It produces both script candidates and likely old-name/renamed-figure candidates.

## Install in the repository root

From `5_geneticsS1`:

```bash
unzip -o additive_channels_figure_repro_audit_v3.zip
cp additive_channels_figure_repro_audit_v3/* .
chmod +x audit_figures.py run_all.sh verify_outputs.py
```

## Recommended first run

Use this from the repository root:

```bash
python audit_figures.py \
  --root . \
  --tex toSubmit/main_paper_with_page_lines.tex \
  --exclude figsPaper2 \
  --exclude oldMain \
  --exclude supportingOnline \
  --exclude channelSwitching \
  --exclude dynamicClosure
```

Do **not** add `--scan-dir` at first. The v3 script will use smart defaults:

```text
toSubmit
code
figures
additiveChannels
revision/additive_channels_final_verification_package
revision/figures
revision/tex/additiveChannels/additiveChannels
revision/tex/additiveChannels/additive_channels_v3_CG_fixed_package
```

It will also add any existing folders mentioned in the TeX `\graphicspath`.

## Files to inspect next

```bash
cat _figure_audit/audit_summary.md
cat _figure_audit/exact_figure_locations.tsv
cat _figure_audit/figure_name_candidates.tsv
cat _figure_audit/candidate_matches.tsv
cat _figure_audit/zip_inventory.tsv
cat _figure_audit/skipped_dirs.tsv
```

`exact_figure_locations.tsv` tells you whether the final TeX filenames already exist somewhere, including inside zip archives.

`figure_name_candidates.tsv` is useful when the final figure was renamed. For example, the TeX may request `figure1_channel.pdf`, while an older script or folder may contain `figure1_channel_concept.pdf` or `additive_channels_curvature_gap_clear.pdf`.

`candidate_matches.tsv` ranks likely code sources for each figure.

`zip_inventory.tsv` is the new file in v3. It records relevant figures and scripts found inside zip archives without extracting them.

## Building the run script

After inspecting the audit, copy the command template:

```bash
cp _figure_audit/commands.template.tsv commands.tsv
```

Edit `commands.tsv`. Replace each `TODO` command with the verified command that creates the expected output. The command can be anything reproducible, for example:

```text
F2	cd revision/additive_channels_final_verification_package && python code/figure2_validation.py && cp figures/figure2_validation.pdf ../../additiveChannels/figures/figure2_validation.pdf	additiveChannels/figures/figure2_validation.pdf	verified	Regenerates from cached parameters and copied to TeX figure path.
```

Then test partially:

```bash
./run_all.sh --skip-todo
```

When all rows are filled:

```bash
./run_all.sh
```

Checksums will be written to:

```text
_repro_logs/output_checksums.tsv
```

## Quick shell helpers

List the final verification package:

```bash
find revision/additive_channels_final_verification_package -maxdepth 5 -type f | sort
```

Look inside zip archives without extracting:

```bash
find revision figures code toSubmit -name '*.zip' -print0 | while IFS= read -r -d '' z; do
  echo "### $z"
  unzip -l "$z" | sed -n '1,120p'
done
```

Find any final figure filenames anywhere outside the heavy folders:

```bash
find . \
  -path './figsPaper2' -prune -o \
  -path './oldMain' -prune -o \
  -path './revision/supportingOnline' -prune -o \
  -type f \( \
    -name 'figure1_channel.pdf' -o \
    -name 'figure2_validation.pdf' -o \
    -name 'figure3_framework.pdf' -o \
    -name 'figure4_trajectory.pdf' -o \
    -name 'figure5_natural_vs_breeding.pdf' -o \
    -name 'multiseed_4trait_moving.png' -o \
    -name 'cv_4trait_moving.png' -o \
    -name 'geom_invariants_4trait_moving.png' \
  \) -print
```
