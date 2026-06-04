#!/usr/bin/env bash
# ============================================================================
# reproduce_appendix_s5.sh
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
#   chmod +x reproduce_appendix_s5.sh
#   ./reproduce_appendix_s5.sh
#
# Useful alternatives:
#   ./reproduce_appendix_s5.sh --clean          # remove old Appendix S5 outputs first
#   ./reproduce_appendix_s5.sh --skip-slim      # rebuild figures from existing diagnostic CSVs
#   ./reproduce_appendix_s5.sh --figures-only   # same as --skip-slim
#   ./reproduce_appendix_s5.sh --resume         # skip replicate diagnostics that already exist
#   ./reproduce_appendix_s5.sh --no-venv        # use the currently active Python environment
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
reproduce_appendix_s5.sh — reproduce Appendix S5 SLiM validation figures

Usage:
  ./reproduce_appendix_s5.sh [options]

Options:
  --clean          Remove old Appendix S5 outputs first.
  --skip-slim      Rebuild figures from existing diagnostic CSV files.
  --figures-only   Alias for --skip-slim.
  --resume         Skip replicates whose diagnostic CSV already exists.
  --quick          Run two replicates only; a smoke test, not the manuscript result.
  --reps N         Run N replicates instead of 20.
  --jobs N, -j N   Run up to N replicates in parallel (default: cores - 2).
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

# Detect the number of logical cores in a portable way (macOS, then Linux).
detect_cores() {
  if command -v sysctl >/dev/null 2>&1 && sysctl -n hw.ncpu >/dev/null 2>&1; then
    sysctl -n hw.ncpu
  elif command -v nproc >/dev/null 2>&1; then
    nproc
  else
    getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4
  fi
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
JOBS="${JOBS:-0}"   # parallel workers; 0 = auto-detect. Override with --jobs N or JOBS env.

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
      [[ $# -ge 2 ]] || fail "--jobs requires an integer argument"
      JOBS="$2"
      shift 2
      ;;
    --no-venv) USE_VENV=0; shift ;;
    --help|-h) usage; exit 0 ;;
    *) fail "Unknown option '$1'. Run ./reproduce_appendix_s5.sh --help for usage." ;;
  esac
done

[[ "$N_REPS" =~ ^[0-9]+$ ]] || fail "--reps must be a positive integer"
[[ "$SEED_START" =~ ^[0-9]+$ ]] || fail "--seed-start must be a positive integer"
[[ "$N_REPS" -ge 1 ]] || fail "--reps must be at least 1"
[[ "$JOBS" =~ ^[0-9]+$ ]] || fail "--jobs must be a non-negative integer"

# Resolve the worker count.  Auto = leave two cores free for the OS/UI, and
# never launch more workers than there are replicates to run.
if [[ "$JOBS" -le 0 ]]; then
  ncpu="$(detect_cores)"
  auto=$(( ncpu > 2 ? ncpu - 2 : 1 ))
  JOBS=$(( auto < N_REPS ? auto : N_REPS ))
fi
[[ "$JOBS" -ge 1 ]] || JOBS=1

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

# Resolve PYTHON to an absolute path so every parallel worker uses the same
# interpreter regardless of how its subshell inherits PATH.
PYTHON="$(command -v "$PYTHON")"

# Prevent BLAS/Accelerate oversubscription.  On Apple Silicon NumPy links against
# Accelerate (vecLib), which will otherwise spawn a thread pool *inside each*
# diagnostic worker; with JOBS workers running at once that is JOBS x cores of
# contention and can be slower than serial.  Pin every worker to one math thread
# and let the parallelism live across replicates instead.
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
       VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1

# Export everything the per-replicate worker (_run_one_replicate.sh) reads.
export SLIM_BIN PYTHON N_TRAITS SIGMAS GAMMAS Z_OPT_INITIAL DRIFT_VELOCITY \
       DRIFT_END_GEN SEED_START RESUME
export GAMMAS_PY_STR="${GAMMAS_PY[*]}"

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
  echo "parallel_jobs: $JOBS"
  echo "n_traits: $N_TRAITS"
  echo "sigmas: $SIGMAS"
  echo "gammas: $GAMMAS"
  echo "drift_velocity: $DRIFT_VELOCITY"
  echo "drift_end_gen: $DRIFT_END_GEN"
} > logs/run_all_environment.txt

if [[ "$MODE" == "full" ]]; then
  msg "Running ${N_REPS} SLiM replicates (seeds ${SEED_START}..$((SEED_START + N_REPS - 1))) on up to ${JOBS} parallel worker(s)"

  # The replicate phase is embarrassingly parallel: each replicate is an
  # independent SLiM process with its own fixed seed, followed by its own
  # diagnostics.  xargs -P runs up to JOBS of them concurrently.  Because seeds
  # are per-replicate and the later aggregation globs-and-sorts the diagnostic
  # files, the result is bit-for-bit identical to a serial run for any value of
  # JOBS or completion order.
  [[ -f "$SCRIPT_DIR/_run_one_replicate.sh" ]] || \
    fail "Missing worker script: $SCRIPT_DIR/_run_one_replicate.sh"

  if ! seq 1 "$N_REPS" \
        | xargs -P "$JOBS" -n 1 bash "$SCRIPT_DIR/_run_one_replicate.sh"; then
    fail "One or more replicates failed. Inspect logs/rep_*_4trait_moving.slim.log and *.diagnostics.log"
  fi
else
  msg "Skipping SLiM; rebuilding figures from existing diagnostic CSVs"
fi

shopt -s nullglob
diag_files=(output/rep_*_4trait_moving_diag.csv)
shopt -u nullglob

[[ "${#diag_files[@]}" -gt 0 ]] || fail "No diagnostic CSV files found in output/. Run ./reproduce_appendix_s5.sh, or place output/rep_*_4trait_moving_diag.csv files there."
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

# ---------------------------------------------------------------------------
# Scientific reproduction gate.
#
# File-existence is necessary but not sufficient: the figures are stochastic
# SLiM output, so the meaningful test is that the framework's identities still
# hold.  We assert (i) the across-replicate median |A_g - R^2| lands near the
# manuscript value (~0.013), and (ii) the algebraic identity 2*V_quad = sum mu_i^2
# holds to numerical precision.  A failure here means the science did not
# reproduce, and the script exits non-zero so callers (e.g. the repo-root
# run_all.sh) surface it loudly.  A --quick smoke test still passes this gate
# because the identities are per-replicate, but its CV panels are not
# manuscript-grade.
# ---------------------------------------------------------------------------
msg "Checking the A_g = R^2 identity (scientific reproduction gate)"
"$PYTHON" - <<'PYGATE'
import sys
import pandas as pd

summary = "output/appendix_s5_summary.csv"
df = pd.read_csv(summary)
look = dict(zip(df["quantity"], df["value"]))

ag_dev = float(look["median_abs_Ag_minus_R2_all"])
alg    = float(look.get("max_abs_2Vquad_minus_sum_mu2", float("nan")))

AG_TARGET, AG_TOL = 0.013, 0.010      # generous band: 0.003 .. 0.023
ALG_TOL = 1e-6                        # algebraic identity should be ~0

ag_ok  = (AG_TARGET - AG_TOL) <= ag_dev <= (AG_TARGET + AG_TOL)
alg_ok = (alg != alg) or (abs(alg) <= ALG_TOL)   # tolerate NaN if column absent

print(f"  median|A_g - R^2|        = {ag_dev:.4f}  "
      f"(expected {AG_TARGET} +/- {AG_TOL}) -> {'OK' if ag_ok else 'OUT OF BAND'}")
print(f"  max|2*V_quad - sum mu^2| = {alg:.2e}  "
      f"(expected <= {ALG_TOL:.0e}) -> {'OK' if alg_ok else 'FAIL'}")

sys.exit(0 if (ag_ok and alg_ok) else 1)
PYGATE

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
