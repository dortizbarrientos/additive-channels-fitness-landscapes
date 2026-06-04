#!/usr/bin/env bash
# =====================================================================
# run_n_traits.sh
#
# Run the EXTENDED scenario:
#   * 4 quantitative traits (configurable via N_TRAITS below)
#   * Initial population at the optimum (z* = (0,0,0,0))
#   * Optimum drifts on trait 1 only, at velocity 0.3/gen, for cycles
#     1..40 inclusive.  After cycle 40 the optimum is fixed.
#
# WHAT TO LOOK FOR IN THE TRAJECTORY:
#   The "rise-then-fall" of A_g (and R^2) is the signature of sustained
#   directional pressure followed by release.  During the drift phase,
#   |b| is held at a non-zero "lag equilibrium" value while G compresses
#   under the Bulmer effect; V_lin grows as 1/G, V_quad shrinks as G^2,
#   so A_g RISES.  After cycle 40, |b| collapses exponentially and A_g
#   FALLS back to ~0.
#
# WHAT TO LOOK FOR IN THE GEOMETRY FIGURE:
#   Top row -- BV cloud snapshots in the (a1, a2) slice at three
#   generations.  The yellow optimum star moves left between gens 1 and
#   40 (drift phase), then stays put.  The cloud chases it.
#   Bottom row -- 4 eigenvalues each for G and Gamma G; only the trait-1
#   direction (lambda_1, mu_1) shows substantial dynamics, the other
#   three traits drift mildly under genetic drift but no sustained
#   compression.  This is the framework's prediction made visual.
#
# Compare with run_one.sh: 2 traits, fixed optimum, "fall-only" A_g.
# =====================================================================

set -euo pipefail

TAG="rep_01_4trait_moving"
SEED=42

BV_OUT="output/${TAG}_bv.csv"
OPT_OUT="output/${TAG}_opt.csv"
DIAG_OUT="output/${TAG}_diag.csv"
FIG_TRAJ="figures/poc_${TAG}.png"
FIG_GEOM="figures/geometry_${TAG}.png"

# ------ Simulation parameters ------
N_TRAITS=4

# Per-trait per-locus effect SDs (initial G = diag(3,2,1,0.5) at HWE)
SIGMAS="c(0.346, 0.283, 0.200, 0.141)"

# Anisotropic stabilising selection
GAMMAS="c(0.10, 0.05, 0.04, 0.03)"

# Initial optimum: at origin, so population starts at the optimum (|b|=0)
Z_OPT_INITIAL="c(0.0, 0.0, 0.0, 0.0)"

# Drift on trait 1 only.  v=0.3/gen for 40 generations gives a 12-unit
# total shift -- under the variance-exhaustion bound (~14 units) for our
# 50-locus, sigma=0.346 setup.
DRIFT_VELOCITY="c(0.3, 0.0, 0.0, 0.0)"
DRIFT_END_GEN=40

# Same gammas as a Python-friendly list for downstream Python scripts
GAMMAS_PY="0.10 0.05 0.04 0.03"

# Snapshot generations: gen 1 (start, |b|=0), gen 40 (end of drift, peak A_g),
# gen 200 (long after drift, A_g returned to ~0).
SNAP1=1
SNAP2=40
SNAP3=200

echo "=========================================="
echo " STEP 1: SLiM simulation (n=${N_TRAITS} traits, moving optimum)"
echo "=========================================="
slim \
    -d "OUTPUT_PATH='${BV_OUT}'" \
    -d "OPTIMUM_PATH='${OPT_OUT}'" \
    -d "SEED=${SEED}" \
    -d "N_TRAITS=${N_TRAITS}" \
    -d "SIGMAS=${SIGMAS}" \
    -d "GAMMAS=${GAMMAS}" \
    -d "Z_OPT_INITIAL=${Z_OPT_INITIAL}" \
    -d "DRIFT_VELOCITY=${DRIFT_VELOCITY}" \
    -d "DRIFT_END_GEN=${DRIFT_END_GEN}" \
    slim_sim_n_traits.slim

echo ""
echo "=========================================="
echo " STEP 2: Compute diagnostics"
echo "=========================================="
python compute_diagnostics.py \
    --bv-input  "${BV_OUT}" \
    --opt-input "${OPT_OUT}" \
    --output    "${DIAG_OUT}" \
    --gammas    ${GAMMAS_PY}

echo ""
echo "=========================================="
echo " STEP 3: Plot trajectory (rise-then-fall A_g)"
echo "=========================================="
python plot_trajectory.py \
    --input  "${DIAG_OUT}" \
    --output "${FIG_TRAJ}"

echo ""
echo "=========================================="
echo " STEP 4: Plot geometry (BV clouds + eigenvalues)"
echo "=========================================="
python plot_geometry.py \
    --bv-input      "${BV_OUT}" \
    --diag-input    "${DIAG_OUT}" \
    --opt-input     "${OPT_OUT}" \
    --output        "${FIG_GEOM}" \
    --gammas        ${GAMMAS_PY} \
    --snapshot-gens "${SNAP1}" "${SNAP2}" "${SNAP3}"

echo ""
echo "=========================================="
echo " Done."
echo "  Trajectory figure:  ${FIG_TRAJ}"
echo "  Geometry figure:    ${FIG_GEOM}"
echo "  Diagnostics CSV:    ${DIAG_OUT}"
echo "  Optimum CSV:        ${OPT_OUT}"
echo "=========================================="
