#!/usr/bin/env bash
# ============================================================================
# run_all.sh
#
# One-command reproduction of the Appendix S5 SLiM validation figures for:
#   Ortiz-Barrientos & Cooper, Additive Channels in Curved Fitness Landscapes
#
# Default behaviour:
#   1. Create/use a local Python virtual environment (.venv).
#   2. Run the 4-trait moving-optimum SLiM simulation for 20 replicates
#      using seeds 42..61.
#   3. Compute diagnostics for each replicate.
#   4. Build the Appendix S5 figures and numerical summary.
#
# Basic use:
#   chmod +x run_all.sh
#   ./run_all.sh
#
# Useful alternatives:
#   ./run_all.sh --clean          # remove old Appendix S5 outputs first
#   ./run_all.sh --skip-slim      # rebuild figures from existing diagnostic CSVs
#   ./run_all.sh --figures-only   # same as --skip-slim
#   ./run_all.sh --resume         # skip replicate diagnostics that already exist
#   ./run_all.sh --no-venv        # use the currently active Python environment
#
# Environment variables:
#   PYTHON_BIN=/path/to/python3   choose Python executable (default: python3)
#   SLIM_BIN=/path/to/slim        choose SLiM executable (default: slim)
#   SLIM=/path/to/slim            also accepted for convenience
#
# Expected outputs:
#   figures/multiseed_4trait_moving.png   and .pdf
#   figures/cv_4trait_moving.png          and .pdf
#   figures/geom_invariants_4trait_moving.png and .pdf
#   output/appendix_s5_summary.csv
#   logs/run_all_environment.txt
#   logs/run_all_manifest.txt
# ============================================================================

set -euo pipefail

usage() {
  cat <<'USAGE'
run_all.sh — reproduce Appendix S5 SLiM validation figures

Usage:
  ./run_all.sh [options]

Options:
  --clean          Remove old Appendix S5 outputs first.
  --skip-slim      Rebuild figures from existing diagnostic CSV files.
  --figures-only   Alias for --skip-slim.
  --resume         Skip replicates whose diagnostic CSV already exists.
  --quick          Run two replicates only; a smoke test, not the manuscript result.
  --reps N         Run N replicates instead of 20.
  --seed-start S   Use S as the first random seed instead of 42.
  --no-venv        Use the current Python environment instead of .venv.
  --help, -h       Show this help message.

Environment variables:
  PYTHON_BIN=/path/to/python3   choose Python executable (default: python3)
  SLIM_BIN=/path/to/slim        choose SLiM executable (default: slim)
  SLIM=/path/to/slim            also accepted for convenience

Expected outputs:
  figures/multiseed_4trait_moving.png   and .pdf
  figures/cv_4trait_moving.png          and .pdf
  figures/geom_invariants_4trait_moving.png and .pdf
  output/appendix_s5_summary.csv
  logs/run_all_environment.txt
  logs/run_all_manifest.txt
USAGE
}

msg() {
  printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

MODE="full"
CLEAN=0
RESUME=0
USE_VENV=1
PYTHON_BIN="${PYTHON_BIN:-python3}"
SLIM_BIN="${SLIM_BIN:-${SLIM:-slim}}"

N_REPS=20
SEED_START=42
PEAK_GEN=40

N_TRAITS=4
SIGMAS="c(0.346, 0.283, 0.200, 0.141)"
GAMMAS="c(0.10, 0.05, 0.04, 0.03)"
Z_OPT_INITIAL="c(0.0, 0.0, 0.0, 0.0)"
DRIFT_VELOCITY="c(0.3, 0.0, 0.0, 0.0)"
DRIFT_END_GEN=40
GAMMAS_PY=(0.10 0.05 0.04 0.03)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --clean) CLEAN=1; shift ;;
    --skip-slim|--figures-only) MODE="figures-only"; shift ;;
    --resume) RESUME=1; shift ;;
    --quick) N_REPS=2; shift ;;
    --reps)
      [[ $# -ge 2 ]] || fail "--reps requires an integer argument"
      N_REPS="$2"
      shift 2
      ;;
    --seed-start)
      [[ $# -ge 2 ]] || fail "--seed-start requires an integer argument"
      SEED_START="$2"
      shift 2
      ;;
    --no-venv) USE_VENV=0; shift ;;
    --help|-h) usage; exit 0 ;;
    *) fail "Unknown option '$1'. Run ./run_all.sh --help for usage." ;;
  esac
done

[[ "$N_REPS" =~ ^[0-9]+$ ]] || fail "--reps must be a positive integer"
[[ "$SEED_START" =~ ^[0-9]+$ ]] || fail "--seed-start must be a positive integer"
[[ "$N_REPS" -ge 1 ]] || fail "--reps must be at least 1"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

for f in slim_sim_n_traits.slim compute_diagnostics.py make_appendix_s5_figures.py requirements.txt; do
  [[ -f "$f" ]] || fail "Required file not found: $f"
done

command -v "$PYTHON_BIN" >/dev/null 2>&1 || fail "Python executable not found: $PYTHON_BIN"
if [[ "$MODE" == "full" ]]; then
  command -v "$SLIM_BIN" >/dev/null 2>&1 || fail "SLiM executable not found: $SLIM_BIN"
fi

mkdir -p output figures logs

if [[ "$CLEAN" -eq 1 ]]; then
  msg "Cleaning previous Appendix S5 outputs"
  rm -f output/rep_*_4trait_moving_bv.csv \
        output/rep_*_4trait_moving_opt.csv \
        output/rep_*_4trait_moving_diag.csv \
        output/appendix_s5_summary.csv
  rm -f figures/multiseed_4trait_moving.* \
        figures/cv_4trait_moving.* \
        figures/geom_invariants_4trait_moving.*
  rm -f logs/rep_*_4trait_moving.slim.log \
        logs/rep_*_4trait_moving.diagnostics.log \
        logs/run_all_environment.txt \
        logs/run_all_manifest.txt
fi

if [[ "$USE_VENV" -eq 1 ]]; then
  if [[ ! -d .venv ]]; then
    msg "Creating Python virtual environment (.venv)"
    "$PYTHON_BIN" -m venv .venv
  else
    msg "Using existing Python virtual environment (.venv)"
  fi
  # shellcheck disable=SC1091
  source .venv/bin/activate
  PYTHON="python"
  msg "Installing Python requirements"
  "$PYTHON" -m pip install --upgrade pip
  "$PYTHON" -m pip install -r requirements.txt
else
  PYTHON="$PYTHON_BIN"
  msg "Using current Python environment: $($PYTHON --version 2>&1)"
fi

msg "Checking Python dependencies"
"$PYTHON" - <<'PYDEPS'
import importlib
for module in ("numpy", "pandas", "matplotlib"):
    importlib.import_module(module)
print("Python dependencies OK")
PYDEPS

{
  echo "Appendix S5 reproduction run"
  echo "date: $(date)"
  echo "mode: $MODE"
  echo "working_directory: $SCRIPT_DIR"
  echo "python: $($PYTHON --version 2>&1)"
  echo "python_path: $(command -v "$PYTHON" || true)"
  if command -v "$SLIM_BIN" >/dev/null 2>&1; then
    echo "slim_path: $(command -v "$SLIM_BIN")"
    echo "slim_version: $($SLIM_BIN -v 2>&1 | head -n 1)"
  else
    echo "slim_path: not found"
  fi
  echo "n_replicates: $N_REPS"
  echo "seeds: ${SEED_START}..$((SEED_START + N_REPS - 1))"
  echo "n_traits: $N_TRAITS"
  echo "sigmas: $SIGMAS"
  echo "gammas: $GAMMAS"
  echo "drift_velocity: $DRIFT_VELOCITY"
  echo "drift_end_gen: $DRIFT_END_GEN"
} > logs/run_all_environment.txt

if [[ "$MODE" == "full" ]]; then
  msg "Running ${N_REPS} SLiM replicates, seeds ${SEED_START}..$((SEED_START + N_REPS - 1))"

  for i in $(seq 1 "$N_REPS"); do
    seed=$((SEED_START + i - 1))
    tag=$(printf "rep_%02d_4trait_moving" "$i")
    bv_out="output/${tag}_bv.csv"
    opt_out="output/${tag}_opt.csv"
    diag_out="output/${tag}_diag.csv"
    slim_log="logs/${tag}.slim.log"
    diag_log="logs/${tag}.diagnostics.log"

    if [[ "$RESUME" -eq 1 && -s "$diag_out" ]]; then
      msg "Replicate ${i}/${N_REPS}: ${tag} already has diagnostics; skipping"
      continue
    fi

    msg "Replicate ${i}/${N_REPS}: seed=${seed}, tag=${tag}"

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

    "$PYTHON" compute_diagnostics.py \
      --bv-input "$bv_out" \
      --opt-input "$opt_out" \
      --output "$diag_out" \
      --gammas "${GAMMAS_PY[@]}" > "$diag_log" 2>&1
  done
else
  msg "Skipping SLiM; rebuilding figures from existing diagnostic CSVs"
fi

shopt -s nullglob
diag_files=(output/rep_*_4trait_moving_diag.csv)
shopt -u nullglob

[[ "${#diag_files[@]}" -gt 0 ]] || fail "No diagnostic CSV files found in output/. Run ./run_all.sh, or place output/rep_*_4trait_moving_diag.csv files there."
if [[ "$MODE" == "full" && "${#diag_files[@]}" -ne "$N_REPS" ]]; then
  fail "Expected ${N_REPS} diagnostic CSV files but found ${#diag_files[@]}. Use --resume only after all missing replicates finish."
fi

msg "Building Appendix S5 figures from ${#diag_files[@]} diagnostic file(s)"
"$PYTHON" make_appendix_s5_figures.py \
  --diag-glob "output/rep_*_4trait_moving_diag.csv" \
  --output-dir figures \
  --peak-gen "$PEAK_GEN" \
  --summary-csv output/appendix_s5_summary.csv

expected=(
  figures/multiseed_4trait_moving.png
  figures/multiseed_4trait_moving.pdf
  figures/cv_4trait_moving.png
  figures/cv_4trait_moving.pdf
  figures/geom_invariants_4trait_moving.png
  figures/geom_invariants_4trait_moving.pdf
  output/appendix_s5_summary.csv
)

msg "Checking outputs"
for f in "${expected[@]}"; do
  [[ -s "$f" ]] || fail "Expected output was not created: $f"
  echo "  OK  $f"
done

{
  echo "Appendix S5 output manifest"
  echo "date: $(date)"
  echo "diagnostic_csv_count: ${#diag_files[@]}"
  echo "figures:"
  echo "  - figures/multiseed_4trait_moving.png"
  echo "  - figures/multiseed_4trait_moving.pdf"
  echo "  - figures/cv_4trait_moving.png"
  echo "  - figures/cv_4trait_moving.pdf"
  echo "  - figures/geom_invariants_4trait_moving.png"
  echo "  - figures/geom_invariants_4trait_moving.pdf"
  echo "summary: output/appendix_s5_summary.csv"
  echo "environment_record: logs/run_all_environment.txt"
  echo "summary_preview:"
  head -n 20 output/appendix_s5_summary.csv | sed 's/^/  /'
} > logs/run_all_manifest.txt

msg "Done"
echo "Created Appendix S5 figures in ./figures and summary in ./output/appendix_s5_summary.csv"
