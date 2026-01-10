#!/usr/bin/env bash
set -euo pipefail

poetry run ruff check .
poetry run ruff format --check .
poetry run pytest
