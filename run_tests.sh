#!/usr/bin/env bash
# Runs every test. Usage: ./run_tests.sh
set -euo pipefail
cd "$(dirname "$0")"
exec .venv/bin/python -m pytest "$@"
