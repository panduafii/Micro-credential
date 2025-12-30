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

# Install dependencies (production only, no dev dependencies)
echo "📦 Installing dependencies..."
poetry install --no-dev --no-interaction --no-ansi

# Run database migrations
echo "🗄️  Running database migrations..."
poetry run alembic upgrade head

echo "✅ Build completed successfully!"
