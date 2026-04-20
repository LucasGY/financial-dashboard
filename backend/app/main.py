from fastapi import FastAPI

from app.api.v1.router import router as api_v1_router
from app.core.exception_handlers import register_exception_handlers


def create_app() -> FastAPI:
    app = FastAPI(title="Financial Dashboard API", version="1.0.0")
    register_exception_handlers(app)
    app.include_router(api_v1_router, prefix="/api/v1")
    return app


app = create_app()
