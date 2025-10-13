# API Documentation
- FastAPI automatically exposes interactive Swagger UI at `/docs` and ReDoc at `/redoc`, powered by the OpenAPI spec above.  
- The canonical YAML lives at `docs/api/openapi.yaml`; regenerate it via `scripts/export-openapi.sh` whenever routes change.  
- CI should diff the FastAPI-generated schema against the committed file to prevent drift.  
- MkDocs (Material theme) can ingest the same YAML to publish static API docs if a marketing/partner portal is needed.
