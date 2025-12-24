from fastapi import FastAPI

from . import health


def register_routes(app: FastAPI) -> None:
    """Attach all API routers to the FastAPI application."""
    app.include_router(health.router)

