#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$repo_dir/examples/estimating_variance_share/environment.sh"
exec "$python_bin" "$example_dir/run_case.py" "$@"

