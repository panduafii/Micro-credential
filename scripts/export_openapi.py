from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from src.api.main import app as api_app


def export_openapi(app: FastAPI, destination: Path) -> None:
    """Persist the OpenAPI schema to the given destination."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    schema = app.openapi()
    destination.write_text(json.dumps(schema, indent=2))


def main() -> None:
    output = Path("docs/api/openapi.json")
    export_openapi(api_app, output)


if __name__ == "__main__":
    main()

