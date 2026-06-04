#!/usr/bin/env bash
# =====================================================================
# run_20_reps_appendix_s5.sh
#
# Reproduce Appendix S5 for:
#   Additive Channels in Curved Fitness Landscapes
#
# This script runs the 4-trait moving-optimum SLiM validation exactly as
# described in Appendix S5: N=2000 diploids, 200 QTLs, 4 traits,
# moving optimum on trait 1 for generations 1--40, and 20 stochastic
# replicates using seeds 42..61.
#
# Required files in the same directory:
#   slim_sim_n_traits.slim
#   compute_diagnostics.py
#   make_appendix_s5_figures.py
#
# Required software:
#   SLiM >= 5.2 on PATH
#   Python with numpy, pandas, matplotlib
# =====================================================================

set -euo pipefail

if ! command -v slim >/dev/null 2>&1; then
    echo "ERROR: slim is not on PATH. Install SLiM >= 5.2 and retry." >&2
    exit 1
fi

mkdir -p output figures

# ---- Appendix S5 parameters ----
N_TRAITS=4
SIGMAS="c(0.346, 0.283, 0.200, 0.141)"
GAMMAS="c(0.10, 0.05, 0.04, 0.03)"
Z_OPT_INITIAL="c(0.0, 0.0, 0.0, 0.0)"
DRIFT_VELOCITY="c(0.3, 0.0, 0.0, 0.0)"
DRIFT_END_GEN=40
GAMMAS_PY="0.10 0.05 0.04 0.03"

echo "======================================================"
echo " Appendix S5 SLiM validation: 20 replicates, seeds 42..61"
echo "======================================================"

for i in $(seq 1 20); do
    seed=$((41 + i))   # i=1 -> 42; i=20 -> 61
    tag=$(printf "rep_%02d_4trait_moving" "$i")

    bv_out="output/${tag}_bv.csv"
    opt_out="output/${tag}_opt.csv"
    diag_out="output/${tag}_diag.csv"

    echo ""
    echo "---- replicate ${i}/20 | seed=${seed} | tag=${tag} ----"

    slim \
        -d "OUTPUT_PATH='${bv_out}'" \
        -d "OPTIMUM_PATH='${opt_out}'" \
        -d "SEED=${seed}" \
        -d "N_TRAITS=${N_TRAITS}" \
        -d "SIGMAS=${SIGMAS}" \
        -d "GAMMAS=${GAMMAS}" \
        -d "Z_OPT_INITIAL=${Z_OPT_INITIAL}" \
        -d "DRIFT_VELOCITY=${DRIFT_VELOCITY}" \
        -d "DRIFT_END_GEN=${DRIFT_END_GEN}" \
        slim_sim_n_traits.slim

    python compute_diagnostics.py \
        --bv-input "${bv_out}" \
        --opt-input "${opt_out}" \
        --output "${diag_out}" \
        --gammas ${GAMMAS_PY}
done

echo ""
echo "======================================================"
echo " Building Appendix S5 figures and numerical summary"
echo "======================================================"

python make_appendix_s5_figures.py \
    --diag-glob "output/rep_*_4trait_moving_diag.csv" \
    --output-dir figures \
    --peak-gen 40 \
    --summary-csv output/appendix_s5_summary.csv

echo ""
echo "Done. Expected manuscript figure files:"
echo "  figures/multiseed_4trait_moving.png"
echo "  figures/cv_4trait_moving.png"
echo "  figures/geom_invariants_4trait_moving.png"
echo "Summary: output/appendix_s5_summary.csv"
