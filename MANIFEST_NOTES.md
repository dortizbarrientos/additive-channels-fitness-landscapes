# Notes for the reviewer-facing repository

The current working directory contains at least three conceptual branches: the GENETICS/Additive Channels manuscript, PNAS dynamics material, and older or parallel figure histories. The reviewer-facing repository should not expose that history as an archaeological task.

A clean final structure should look like this:

```text
additive-channels-genetics/
  README.md
  run_all.sh
  commands.tsv
  main_paper_with_page_lines.tex
  additiveChannels/
    figures/
      figure1_channel.pdf
      figure2_validation.pdf
      figure3_framework.pdf
      figure4_trajectory.pdf
      figure5_natural_vs_breeding.pdf
      multiseed_4trait_moving.png
      cv_4trait_moving.png
      geom_invariants_4trait_moving.png
    code/
      figure1_channel/
      figure2_validation/
      figure3_framework/
      figure4_trajectory/
      figure5_natural_vs_breeding/
      appendix_s5_simulation/
    data/
      appendix_s5_cached_replicates/
```

For each figure, record whether it is regenerated from raw code, regenerated from cached stochastic simulation output, or copied from an editable composition file after script-generated panels are created. That distinction is fine, but it should be explicit.
