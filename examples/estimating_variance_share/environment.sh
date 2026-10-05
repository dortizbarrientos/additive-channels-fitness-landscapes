#!/usr/bin/env bash
# Shared setup for the two repository launch commands.
set -euo pipefail
example_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd -- "$example_dir/../.." && pwd)"
python_bin="${PYTHON_BIN:-python3}"
environment_dir="$repo_dir/.venv-estimation"
if [[ ! -x "$environment_dir/bin/python" ]]; then
  "$python_bin" -m venv "$environment_dir"
fi
python_bin="$environment_dir/bin/python"
if [[ ! -f "$environment_dir/requirements-installed.txt" ]] || ! cmp -s "$example_dir/requirements.txt" "$environment_dir/requirements-installed.txt"; then
  "$python_bin" -m pip install -r "$example_dir/requirements.txt"
  cp "$example_dir/requirements.txt" "$environment_dir/requirements-installed.txt"
fi
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg

