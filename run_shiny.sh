#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$repo_dir/examples/estimating_variance_share/environment.sh"
exec "$python_bin" -m shiny run --host 127.0.0.1 --port "${SHINY_PORT:-8000}" --launch-browser "$@" "$example_dir/app.py"

