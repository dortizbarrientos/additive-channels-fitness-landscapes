# Appendix S5 SLiM reproduction patch

This small add-on turns the uploaded `slim_validation` folder from a one-replicate proof-of-concept into the full Appendix S5 reproduction workflow described in the manuscript.

Copy these two files into the root of `slim_validation/`:

- `run_20_reps_appendix_s5.sh`
- `make_appendix_s5_figures.py`

Then run:

```bash
cd slim_validation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
chmod +x run_20_reps_appendix_s5.sh
./run_20_reps_appendix_s5.sh
```

Expected manuscript figure outputs:

- `figures/multiseed_4trait_moving.png`
- `figures/cv_4trait_moving.png`
- `figures/geom_invariants_4trait_moving.png`

Expected data outputs:

- `output/rep_01_4trait_moving_bv.csv` through `output/rep_20_4trait_moving_bv.csv`
- matching `_opt.csv` and `_diag.csv` files
- `output/appendix_s5_summary.csv`

For repository submission, do **not** include `.venv/` or `__MACOSX/` artefacts. Keep source scripts, the SLiM file, `requirements.txt`, the README/design notes, the three Appendix S5 figures, and either the per-replicate output CSVs or a clear archive/Zenodo deposit containing them.
