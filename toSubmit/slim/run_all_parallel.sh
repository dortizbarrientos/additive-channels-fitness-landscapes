#!/usr/bin/env bash
# ============================================================================
# run_all.sh
#
# One-command, parallel reproduction of the Appendix S5 SLiM validation figures
# for:
#   Ortiz-Barrientos & Cooper, Additive Channels in Curved Fitness Landscapes
#
# Default behaviour:
#   1. Create/use a local Python virtual environment (.venv).
#   2. Run the 4-trait moving-optimum SLiM simulation for 20 independent
#      replicates using seeds 42..61.
#   3. Run diagnostics for each replicate.
#   4. Build the Appendix S5 figures and numerical summary.
#
# Parallelism:
#   - Replicates are independent, so the script runs them in parallel.
#   - By default, --jobs auto uses all detected CPU cores minus two, capped by
#     the number of replicates. On a large Apple Silicon workstation this will
#     normally run nearly all 20 manuscript replicates simultaneously.
#   - Use --jobs N to choose a specific number of concurrent replicates.
#
# Basic use:
#   chmod +x run_all.sh
#   ./run_all.sh
#
# For a high-core workstation, for example a Mac Studio/Mac Pro M2 Ultra:
#   ./run_all.sh --clean --jobs 20
#
# Useful alternatives:
#   ./run_all.sh --quick                 # two-replicate smoke test
#   ./run_all.sh --resume --jobs auto    # continue an interrupted run
#   ./run_all.sh --skip-slim             # rebuild figures from existing CSVs
#   ./run_all.sh --serial                # run one replicate at a time
#
# Environment variables:
#   PYTHON_BIN=/path/to/python3   choose Python executable (default: python3)
#   SLIM_BIN=/path/to/slim        choose SLiM executable (default: slim)
#   SLIM=/path/to/slim            also accepted for convenience
#   JOBS=N                        choose default parallel jobs without --jobs
#
# Expected outputs:
#   figures/multiseed_4trait_moving.png        and .pdf
#   figures/cv_4trait_moving.png               and .pdf
#   figures/geom_invariants_4trait_moving.png  and .pdf
#   output/appendix_s5_summary.csv
#   logs/run_all_environment.txt
#   logs/run_all_manifest.txt
#   logs/run_all_parallel_status.tsv
# ============================================================================

set -euo pipefail

usage() {
  cat <<'USAGE'
run_all.sh — reproduce Appendix S5 SLiM validation figures in parallel

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
  --jobs N         Run N replicate jobs concurrently.
  -j N             Alias for --jobs N.
  --jobs auto      Auto-detect cores and leave two cores free. This is the default.
  --serial         Alias for --jobs 1.
  --no-venv        Use the current Python environment instead of .venv.
  --help, -h       Show this help message.

Environment variables:
  PYTHON_BIN=/path/to/python3   choose Python executable (default: python3)
  SLIM_BIN=/path/to/slim        choose SLiM executable (default: slim)
  SLIM=/path/to/slim            also accepted for convenience
  JOBS=N                        choose default parallel jobs without --jobs

Examples:
  ./run_all.sh
  ./run_all.sh --clean --jobs 20
  ./run_all.sh --resume --jobs auto
  ./run_all.sh --quick --jobs 2
  SLIM=/Applications/SLiM.app/Contents/MacOS/slim ./run_all.sh -j 20

Expected outputs:
  figures/multiseed_4trait_moving.png        and .pdf
  figures/cv_4trait_moving.png               and .pdf
  figures/geom_invariants_4trait_moving.png  and .pdf
  output/appendix_s5_summary.csv
  logs/run_all_environment.txt
  logs/run_all_manifest.txt
  logs/run_all_parallel_status.tsv
USAGE
}

msg() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

detect_cores() {
  # macOS / Apple Silicon
  if command -v sysctl >/dev/null 2>&1; then
    local n
    n="$(sysctl -n hw.ncpu 2>/dev/null || true)"
    if [[ "$n" =~ ^[0-9]+$ && "$n" -ge 1 ]]; then
      echo "$n"
      return 0
    fi
  fi

  # Linux / POSIX fallback
  if command -v getconf >/dev/null 2>&1; then
    local n
    n="$(getconf _NPROCESSORS_ONLN 2>/dev/null || true)"
    if [[ "$n" =~ ^[0-9]+$ && "$n" -ge 1 ]]; then
      echo "$n"
      return 0
    fi
  fi

  echo 1
}

active_job_count() {
  jobs -pr | wc -l | tr -d '[:space:]'
}

throttle_jobs() {
  local max_jobs="$1"
  while [[ "$(active_job_count)" -ge "$max_jobs" ]]; do
    sleep 1
  done
}

write_parallel_status_manifest() {
  mkdir -p logs
  {
    echo -e "status\treplicate\tseed\truntime_seconds\tbv_csv\toptimum_csv\tdiagnostic_csv\tnote"
    if [[ -d logs/status ]]; then
      find logs/status -name '*.tsv' -type f | sort | while read -r f; do
        cat "$f"
      done
    fi
  } > logs/run_all_parallel_status.tsv
}

MODE="full"
CLEAN=0
RESUME=0
USE_VENV=1
PYTHON_BIN="${PYTHON_BIN:-python3}"
SLIM_BIN="${SLIM_BIN:-${SLIM:-slim}}"
JOBS_REQUESTED="${JOBS:-auto}"

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
    --jobs|-j)
      [[ $# -ge 2 ]] || fail "--jobs requires an integer argument or 'auto'"
      JOBS_REQUESTED="$2"
      shift 2
      ;;
    --serial) JOBS_REQUESTED=1; shift ;;
    --no-venv) USE_VENV=0; shift ;;
    --help|-h) usage; exit 0 ;;
    *) fail "Unknown option '$1'. Run ./run_all.sh --help for usage." ;;
  esac
done

[[ "$N_REPS" =~ ^[0-9]+$ ]] || fail "--reps must be a positive integer"
[[ "$SEED_START" =~ ^[0-9]+$ ]] || fail "--seed-start must be a positive integer"
[[ "$N_REPS" -ge 1 ]] || fail "--reps must be at least 1"

DETECTED_CORES="$(detect_cores)"
if [[ "$JOBS_REQUESTED" == "auto" ]]; then
  if [[ "$DETECTED_CORES" -gt 2 ]]; then
    JOBS_RESOLVED=$((DETECTED_CORES - 2))
  else
    JOBS_RESOLVED=1
  fi
else
  [[ "$JOBS_REQUESTED" =~ ^[0-9]+$ ]] || fail "--jobs must be a positive integer or 'auto'"
  [[ "$JOBS_REQUESTED" -ge 1 ]] || fail "--jobs must be at least 1"
  JOBS_RESOLVED="$JOBS_REQUESTED"
fi

# More concurrent jobs than replicates only adds clutter.
if [[ "$JOBS_RESOLVED" -gt "$N_REPS" ]]; then
  JOBS_RESOLVED="$N_REPS"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

for f in slim_sim_n_traits.slim compute_diagnostics.py make_appendix_s5_figures.py requirements.txt; do
  [[ -f "$f" ]] || fail "Required file not found: $f"
done

command -v "$PYTHON_BIN" >/dev/null 2>&1 || fail "Python executable not found: $PYTHON_BIN"
if [[ "$MODE" == "full" ]]; then
  command -v "$SLIM_BIN" >/dev/null 2>&1 || fail "SLiM executable not found: $SLIM_BIN"
fi

# Prevent many simultaneous Python diagnostic processes from each trying to use
# several BLAS/Accelerate threads. Users can override these before running.
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"
export OPENBLAS_NUM_THREADS="${OPENBLAS_NUM_THREADS:-1}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-1}"
export VECLIB_MAXIMUM_THREADS="${VECLIB_MAXIMUM_THREADS:-1}"
export NUMEXPR_NUM_THREADS="${NUMEXPR_NUM_THREADS:-1}"

mkdir -p output figures logs logs/status

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
        logs/run_all_manifest.txt \
        logs/run_all_parallel_status.tsv
  rm -rf logs/status
  mkdir -p logs/status
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
  echo "detected_cpu_cores: $DETECTED_CORES"
  echo "parallel_jobs: $JOBS_RESOLVED"
  echo "parallel_jobs_requested: $JOBS_REQUESTED"
  echo "n_replicates: $N_REPS"
  echo "seeds: ${SEED_START}..$((SEED_START + N_REPS - 1))"
  echo "n_traits: $N_TRAITS"
  echo "sigmas: $SIGMAS"
  echo "gammas: $GAMMAS"
  echo "drift_velocity: $DRIFT_VELOCITY"
  echo "drift_end_gen: $DRIFT_END_GEN"
  echo "OMP_NUM_THREADS: $OMP_NUM_THREADS"
  echo "OPENBLAS_NUM_THREADS: $OPENBLAS_NUM_THREADS"
  echo "MKL_NUM_THREADS: $MKL_NUM_THREADS"
  echo "VECLIB_MAXIMUM_THREADS: $VECLIB_MAXIMUM_THREADS"
  echo "NUMEXPR_NUM_THREADS: $NUMEXPR_NUM_THREADS"
} > logs/run_all_environment.txt

run_replicate() {
  set +e

  local i="$1"
  local seed="$2"
  local tag="$3"
  local bv_out="output/${tag}_bv.csv"
  local opt_out="output/${tag}_opt.csv"
  local diag_out="output/${tag}_diag.csv"
  local slim_log="logs/${tag}.slim.log"
  local diag_log="logs/${tag}.diagnostics.log"
  local status_file="logs/status/${tag}.tsv"
  local start_epoch end_epoch runtime rc

  start_epoch="$(date +%s)"

  if [[ "$RESUME" -eq 1 && -s "$diag_out" ]]; then
    end_epoch="$(date +%s)"
    runtime=$((end_epoch - start_epoch))
    printf 'skipped\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$tag" "$seed" "$runtime" "$bv_out" "$opt_out" "$diag_out" \
      "diagnostic CSV already exists; --resume active" > "$status_file"
    msg "SKIP ${i}/${N_REPS}: ${tag} already has diagnostics"
    return 0
  fi

  msg "START ${i}/${N_REPS}: ${tag}, seed=${seed}"

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
  rc=$?
  if [[ "$rc" -ne 0 ]]; then
    end_epoch="$(date +%s)"
    runtime=$((end_epoch - start_epoch))
    printf 'failed_slim\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$tag" "$seed" "$runtime" "$bv_out" "$opt_out" "$diag_out" \
      "SLiM exited with status ${rc}; see ${slim_log}" > "$status_file"
    msg "FAIL ${i}/${N_REPS}: ${tag} during SLiM; see ${slim_log}"
    return "$rc"
  fi

  "$PYTHON" compute_diagnostics.py \
    --bv-input "$bv_out" \
    --opt-input "$opt_out" \
    --output "$diag_out" \
    --gammas "${GAMMAS_PY[@]}" > "$diag_log" 2>&1
  rc=$?
  if [[ "$rc" -ne 0 ]]; then
    end_epoch="$(date +%s)"
    runtime=$((end_epoch - start_epoch))
    printf 'failed_diagnostics\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$tag" "$seed" "$runtime" "$bv_out" "$opt_out" "$diag_out" \
      "diagnostics exited with status ${rc}; see ${diag_log}" > "$status_file"
    msg "FAIL ${i}/${N_REPS}: ${tag} during diagnostics; see ${diag_log}"
    return "$rc"
  fi

  end_epoch="$(date +%s)"
  runtime=$((end_epoch - start_epoch))
  printf 'success\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$tag" "$seed" "$runtime" "$bv_out" "$opt_out" "$diag_out" \
    "completed" > "$status_file"
  msg "DONE ${i}/${N_REPS}: ${tag} in ${runtime}s"
  return 0
}

if [[ "$MODE" == "full" ]]; then
  msg "Running ${N_REPS} SLiM replicates, seeds ${SEED_START}..$((SEED_START + N_REPS - 1)), with ${JOBS_RESOLVED} parallel job(s)"

  pids=()
  i=1
  while [[ "$i" -le "$N_REPS" ]]; do
    seed=$((SEED_START + i - 1))
    tag=$(printf "rep_%02d_4trait_moving" "$i")

    throttle_jobs "$JOBS_RESOLVED"
    run_replicate "$i" "$seed" "$tag" &
    pids+=("$!")

    i=$((i + 1))
  done

  failures=0
  for pid in "${pids[@]}"; do
    if ! wait "$pid"; then
      failures=$((failures + 1))
    fi
  done

  write_parallel_status_manifest

  if [[ "$failures" -ne 0 ]]; then
    fail "${failures} replicate job(s) failed. See logs/run_all_parallel_status.tsv and logs/rep_* logs. Re-run with --resume after fixing the issue."
  fi
else
  msg "Skipping SLiM; rebuilding figures from existing diagnostic CSVs"
fi

shopt -s nullglob
diag_files=(output/rep_*_4trait_moving_diag.csv)
shopt -u nullglob

[[ "${#diag_files[@]}" -gt 0 ]] || fail "No diagnostic CSV files found in output/. Run ./run_all.sh, or place output/rep_*_4trait_moving_diag.csv files there."
if [[ "$MODE" == "full" && "${#diag_files[@]}" -ne "$N_REPS" ]]; then
  write_parallel_status_manifest
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

write_parallel_status_manifest

{
  echo "Appendix S5 output manifest"
  echo "date: $(date)"
  echo "diagnostic_csv_count: ${#diag_files[@]}"
  echo "parallel_jobs: $JOBS_RESOLVED"
  echo "detected_cpu_cores: $DETECTED_CORES"
  echo "figures:"
  echo "  - figures/multiseed_4trait_moving.png"
  echo "  - figures/multiseed_4trait_moving.pdf"
  echo "  - figures/cv_4trait_moving.png"
  echo "  - figures/cv_4trait_moving.pdf"
  echo "  - figures/geom_invariants_4trait_moving.png"
  echo "  - figures/geom_invariants_4trait_moving.pdf"
  echo "summary: output/appendix_s5_summary.csv"
  echo "environment_record: logs/run_all_environment.txt"
  echo "parallel_status: logs/run_all_parallel_status.tsv"
  echo "summary_preview:"
  head -n 20 output/appendix_s5_summary.csv | sed 's/^/  /'
} > logs/run_all_manifest.txt

msg "Done"
echo "Created Appendix S5 figures in ./figures and summary in ./output/appendix_s5_summary.csv"
echo "Parallel status written to ./logs/run_all_parallel_status.tsv"
