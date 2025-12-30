#!/usr/bin/env bash
# Render build script - runs during deployment

set -e  # Exit on error

echo "🚀 Starting Render build process..."

# Install Poetry
echo "📦 Installing Poetry..."
pip install --upgrade pip
pip install poetry==${POETRY_VERSION:-1.8.4}

# Configure Poetry for production
poetry config virtualenvs.create false

# Install ALL dependencies (including dev for linting)
echo "📦 Installing dependencies..."
poetry install --no-interaction --no-ansi

# Format and lint check (auto-fix any issues)
echo "🔍 Running code formatting..."
poetry run ruff format .
poetry run ruff check . --fix || true

# Run database migrations
echo "🗄️  Running database migrations..."
poetry run alembic upgrade head

echo "✅ Build completed successfully!"
