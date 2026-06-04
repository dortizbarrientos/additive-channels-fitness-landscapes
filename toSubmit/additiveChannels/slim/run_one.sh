#!/usr/bin/env bash
# =====================================================================
# run_one.sh
#
# Run the SIMPLE PoC (2 traits, fixed optimum) end-to-end:
#   1. SLiM simulation (one replicate, weak + sustained selection)
#   2. Compute diagnostics from the resulting CSV
#   3. Produce the trajectory sanity-check figure (A_g vs R^2 etc.)
#   4. Produce the geometry figure (BV clouds, G eigenvalues, mu_i)
#
# This calls slim_sim.slim (the original 2-trait simple script).
# For the n-trait + moving-optimum extended scenario, use run_n_traits.sh.
#
# Note: Uses the GENERALISED compute_diagnostics.py and plot_geometry.py
# (auto-detect n_traits, accept --gammas vector and --z-opt-static).
# =====================================================================

set -euo pipefail

TAG="rep_01_weak_sustained"
SEED=42

SIM_OUT="output/${TAG}.csv"
DIAG_OUT="output/diag_${TAG}.csv"
FIG_TRAJ="figures/poc_${TAG}.png"
FIG_GEOM="figures/geometry_${TAG}.png"

# 2-trait gammas as a Python-friendly list
GAMMAS_PY="0.10 0.05"

# Static optimum
Z_OPT_PY="-2.0 0.0"

# Snapshot generations for the geometry plot
SNAP1=1
SNAP2=5
SNAP3=100

echo "=========================================="
echo " STEP 1: SLiM simulation"
echo "=========================================="
slim \
    -d "OUTPUT_PATH='${SIM_OUT}'" \
    -d "SEED=${SEED}" \
    slim_sim.slim

echo ""
echo "=========================================="
echo " STEP 2: Compute diagnostics (incl. eigenvalues)"
echo "=========================================="
python compute_diagnostics.py \
    --bv-input      "${SIM_OUT}" \
    --output        "${DIAG_OUT}" \
    --gammas        ${GAMMAS_PY} \
    --z-opt-static  ${Z_OPT_PY}

echo ""
echo "=========================================="
echo " STEP 3: Plot trajectory (validation)"
echo "=========================================="
python plot_trajectory.py \
    --input  "${DIAG_OUT}" \
    --output "${FIG_TRAJ}"

echo ""
echo "=========================================="
echo " STEP 4: Plot geometry (BV clouds + eigenvalues)"
echo "=========================================="
python plot_geometry.py \
    --bv-input      "${SIM_OUT}" \
    --diag-input    "${DIAG_OUT}" \
    --output        "${FIG_GEOM}" \
    --gammas        ${GAMMAS_PY} \
    --z-opt         ${Z_OPT_PY} \
    --snapshot-gens "${SNAP1}" "${SNAP2}" "${SNAP3}"

echo ""
echo "=========================================="
echo " Done."
echo "  Validation figure: ${FIG_TRAJ}"
echo "  Geometry figure:   ${FIG_GEOM}"
echo "=========================================="
