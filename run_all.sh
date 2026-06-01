#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=0
SKIP_TODO=0

# Prefer the active virtual environment's python. If there is no `python`, fall back to python3.
if [[ -z "${PYTHON_BIN:-}" ]]; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    PYTHON_BIN="python3"
  fi
fi
export PYTHON_BIN

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --skip-todo) SKIP_TODO=1 ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Usage: ./run_all.sh [--dry-run] [--skip-todo]" >&2
      exit 2
      ;;
  esac
done

MANIFEST="commands.tsv"
LOGDIR="_repro_logs"
mkdir -p "$LOGDIR"

if [[ ! -f "$MANIFEST" ]]; then
  echo "ERROR: missing $MANIFEST" >&2
  exit 1
fi

echo "Using manifest: $MANIFEST"
echo "Logs: $LOGDIR"
echo "Python: $($PYTHON_BIN -c 'import sys; print(sys.executable)')"

n=0
while IFS=$'\t' read -r figure_id command expected_outputs status notes; do
  # Skip header and empty rows.
  [[ "${figure_id:-}" == "figure_id" ]] && continue
  [[ -z "${figure_id:-}" ]] && continue

  if [[ "$command" == "TODO" ]]; then
    if [[ "$SKIP_TODO" -eq 1 ]]; then
      echo "SKIP $figure_id: TODO command not filled in."
      continue
    fi
    echo "ERROR: $figure_id still has TODO command. Edit commands.tsv or run ./run_all.sh --skip-todo." >&2
    exit 1
  fi

  echo ""
  echo "===== $figure_id [$status] ====="
  echo "$command"

  if [[ "$DRY_RUN" -eq 0 ]]; then
    log="$LOGDIR/${figure_id}.log"
    # Use bash -c, not bash -lc, so we do not reset the activated virtual-environment PATH.
    if ! bash -c "$command" > "$log" 2>&1; then
      echo "ERROR: command failed for $figure_id. See $log" >&2
      echo "----- tail of $log -----" >&2
      tail -80 "$log" >&2 || true
      exit 1
    fi
  fi
  n=$((n + 1))
done < "$MANIFEST"

if [[ "$DRY_RUN" -eq 0 ]]; then
  "$PYTHON_BIN" verify_outputs.py --manifest "$MANIFEST" --out "$LOGDIR/output_checksums.tsv"
  echo ""
  echo "Done. Checksums written to $LOGDIR/output_checksums.tsv"
else
  echo ""
  echo "Dry run complete. No commands executed. Commands read: $n"
fi
