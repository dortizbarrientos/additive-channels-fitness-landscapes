#!/usr/bin/env bash
# Reproduce all figures listed in commands.tsv.
#
# Usage:
#   ./run_all.sh                  # require every command to be filled
#   ./run_all.sh --skip-todo      # run completed rows and skip TODO rows
#   ./run_all.sh --dry-run        # print commands without running
#   COMMANDS_FILE=my.tsv ./run_all.sh --skip-todo
#
# commands.tsv columns:
#   figure_id<TAB>command<TAB>expected_outputs<TAB>status<TAB>notes
# expected_outputs may contain comma-separated paths.

set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

COMMANDS_FILE="${COMMANDS_FILE:-commands.tsv}"
LOG_DIR="${LOG_DIR:-_repro_logs}"
SKIP_TODO=0
DRY_RUN=0

for arg in "$@"; do
  case "$arg" in
    --skip-todo) SKIP_TODO=1 ;;
    --dry-run) DRY_RUN=1 ;;
    *) echo "ERROR: unknown argument: $arg" >&2; exit 2 ;;
  esac
done

if [[ "${ALLOW_TODO:-0}" == "1" ]]; then
  SKIP_TODO=1
fi

if [[ ! -f "$COMMANDS_FILE" ]]; then
  if [[ -f "_figure_audit/commands.template.tsv" ]]; then
    echo "No commands.tsv found. Creating one from _figure_audit/commands.template.tsv" >&2
    cp _figure_audit/commands.template.tsv commands.tsv
    COMMANDS_FILE="commands.tsv"
  else
    echo "ERROR: Cannot find $COMMANDS_FILE in $(pwd). Run audit_figures.py first or set COMMANDS_FILE." >&2
    exit 2
  fi
fi

mkdir -p "$LOG_DIR" additiveChannels/figures

ran=0
skipped=0
failed=0

# Avoid a pipeline subshell so counters persist.
{
  read -r header || true
  while IFS=$'\t' read -r figure_id command expected_outputs status notes || [[ -n "${figure_id:-}" ]]; do
    [[ -z "${figure_id:-}" ]] && continue
    [[ "${figure_id:0:1}" == "#" ]] && continue

    if [[ "${command}" == "TODO" || "${status}" == "TODO" ]]; then
      if [[ "$SKIP_TODO" == "1" ]]; then
        echo "SKIP ${figure_id}: TODO command not filled in."
        skipped=$((skipped + 1))
        continue
      else
        echo "ERROR: ${figure_id} still has TODO command. Edit commands.tsv, or run ./run_all.sh --skip-todo for partial testing." >&2
        exit 3
      fi
    fi

    log_file="$LOG_DIR/${figure_id}.log"
    echo "=== ${figure_id} ==="
    echo "Command: ${command}"
    echo "Expected: ${expected_outputs}"
    echo "Log: ${log_file}"

    if [[ "$DRY_RUN" == "1" ]]; then
      ran=$((ran + 1))
      continue
    fi

    set +e
    bash -lc "$command" >"$log_file" 2>&1
    rc=$?
    set -e
    if [[ $rc -ne 0 ]]; then
      echo "FAILED ${figure_id} with exit code ${rc}. See ${log_file}" >&2
      failed=$((failed + 1))
      continue
    fi

    # Verify expected outputs for this row immediately.
    IFS=',' read -ra outs <<< "$expected_outputs"
    missing=0
    for out in "${outs[@]}"; do
      out_trimmed="$(echo "$out" | sed 's/^ *//;s/ *$//')"
      if [[ -z "$out_trimmed" ]]; then
        continue
      fi
      if [[ ! -s "$out_trimmed" ]]; then
        echo "MISSING ${figure_id}: expected output not found or empty: $out_trimmed" >&2
        missing=1
      fi
    done
    if [[ "$missing" == "1" ]]; then
      failed=$((failed + 1))
      continue
    fi
    ran=$((ran + 1))
  done
} < "$COMMANDS_FILE"

if [[ "$DRY_RUN" != "1" ]]; then
  ${PYTHON_BIN} verify_outputs.py --commands "$COMMANDS_FILE" --out "$LOG_DIR/output_checksums.tsv"
fi

echo "Done. Ran ${ran} command(s), skipped ${skipped} TODO row(s), failed ${failed}. Logs are in ${LOG_DIR}."
if [[ $failed -ne 0 ]]; then
  exit 4
fi
