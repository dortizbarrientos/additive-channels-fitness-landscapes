#!/usr/bin/env bash
# ============================================================================
# _run_one_replicate.sh
#
# Runs ONE Appendix S5 replicate end to end: a single SLiM simulation followed
# by its per-generation diagnostics.  It is the unit of work that
# reproduce_appendix_s5.sh launches in parallel via `xargs -P`.
#
# It is deliberately small and side-effect-isolated: it writes only this
# replicate's own files (output/rep_NN_* and logs/rep_NN_*), so any number of
# copies can run concurrently without contention.
#
# It is NOT meant to be called directly; reproduce_appendix_s5.sh exports the
# model parameters and tool paths it reads.  Calling it standalone will fail on
# the env-var checks below, which is intentional.
#
# Argument:
#   $1  replicate index i (1-based).  Seed = SEED_START + i - 1.
# ============================================================================

set -euo pipefail

i="${1:?internal error: replicate index not provided}"

# --- Inherited from the parent driver (fail loudly if missing) -------------
: "${SLIM_BIN:?_run_one_replicate.sh must be launched by reproduce_appendix_s5.sh}"
: "${PYTHON:?missing PYTHON}"
: "${N_TRAITS:?}" "${SIGMAS:?}" "${GAMMAS:?}" "${Z_OPT_INITIAL:?}"
: "${DRIFT_VELOCITY:?}" "${DRIFT_END_GEN:?}" "${SEED_START:?}" "${GAMMAS_PY_STR:?}"
RESUME="${RESUME:-0}"

# Operate in the worker script's own directory so relative paths resolve the
# same way they do for the parent (output/, logs/).
cd "$(dirname "$0")"

seed=$((SEED_START + i - 1))
tag=$(printf "rep_%02d_4trait_moving" "$i")
bv_out="output/${tag}_bv.csv"
opt_out="output/${tag}_opt.csv"
diag_out="output/${tag}_diag.csv"
slim_log="logs/${tag}.slim.log"
diag_log="logs/${tag}.diagnostics.log"

if [[ "$RESUME" -eq 1 && -s "$diag_out" ]]; then
  echo "[rep ${i}] resume: ${diag_out} exists, skipping"
  exit 0
fi

echo "[rep ${i}] seed=${seed} -> SLiM"
"$SLIM_BIN" \
  -d "OUTPUT_PATH='${bv_out}'" \
  -d "OPTIMUM_PATH='${opt_out}'" \
  -d "SEED=${seed}" \
  -d "N_TRAITS=${N_TRAITS}" \
  -d "SIGMAS=${SIGMAS}" \
  -d "GAMMAS=${GAMMAS}" \
  -d "Z_OPT_INITIAL=${Z_OPT_INITIAL}" \
  -d "DRIFT_VELOCITY=${DRIFT_VELOCITY}" \
  -d "DRIFT_END_GEN=${DRIFT_END_GEN}" \
  slim_sim_n_traits.slim > "$slim_log" 2>&1

echo "[rep ${i}] seed=${seed} -> diagnostics"
# GAMMAS_PY_STR is an intentionally word-split list of per-trait gammas.
# shellcheck disable=SC2086
"$PYTHON" compute_diagnostics.py \
  --bv-input "$bv_out" \
  --opt-input "$opt_out" \
  --output "$diag_out" \
  --gammas $GAMMAS_PY_STR > "$diag_log" 2>&1

echo "[rep ${i}] done"
