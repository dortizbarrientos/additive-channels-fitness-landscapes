#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=0
SKIP_TODO=0

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

if [[ -z "${PYTHON_BIN:-}" ]]; then
  if [[ -n "${VIRTUAL_ENV:-}" && -x "$VIRTUAL_ENV/bin/python" ]]; then
    PYTHON_BIN="$VIRTUAL_ENV/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
  else
    echo "ERROR: could not find python3 or python. Create/activate a virtual environment first." >&2
    exit 1
  fi
fi
export PYTHON_BIN

echo "Using manifest: $MANIFEST"
echo "Logs: $LOGDIR"
echo "Python: $PYTHON_BIN"

commands_read=0
while IFS=$'\t' read -r figure_id command expected_outputs status notes; do
  [[ -z "${figure_id:-}" ]] && continue
  [[ "$figure_id" == "figure_id" ]] && continue
  commands_read=$((commands_read + 1))

  if [[ "$command" == "TODO" ]]; then
    if [[ "$SKIP_TODO" -eq 1 ]]; then
      echo "SKIP $figure_id: TODO command not filled in."
      continue
    else
      echo "ERROR: $figure_id still has TODO command. Edit commands.tsv or run ./run_all.sh --skip-todo." >&2
      exit 1
    fi
  fi

  echo ""
  echo "===== $figure_id [$status] ====="
  echo "$command"

  if [[ "$DRY_RUN" -eq 0 ]]; then
    if ! bash -c "$command" > "$LOGDIR/${figure_id}.log" 2>&1; then
      echo "ERROR: command failed for $figure_id. See $LOGDIR/${figure_id}.log" >&2
      echo "----- tail of $LOGDIR/${figure_id}.log -----" >&2
      tail -40 "$LOGDIR/${figure_id}.log" >&2 || true
      exit 1
    fi
  fi
done < "$MANIFEST"

if [[ "$DRY_RUN" -eq 0 ]]; then
  "$PYTHON_BIN" verify_outputs.py --manifest "$MANIFEST" --out "$LOGDIR/output_checksums.tsv"
  echo ""
  echo "Done. Checksums written to $LOGDIR/output_checksums.tsv"
else
  echo ""
  echo "Dry run complete. No commands executed. Commands read: $commands_read"
fi
