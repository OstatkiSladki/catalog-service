from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api import api_router
from src.config.logging import configure_logging
from src.config.settings import Settings, get_settings
from src.db.session import DatabaseSessionManager
from src.middleware.error_handler import register_exception_handlers
from src.middleware.request_context import RequestContextMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
  app_settings = settings or get_settings()
  configure_logging(app_settings)

  @asynccontextmanager
  async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    session_manager = DatabaseSessionManager.from_settings(app_settings)
    app.state.session_manager = session_manager
    try:
      yield
    finally:
      await session_manager.close()

  app = FastAPI(
    title=app_settings.app_name,
    version=app_settings.app_version,
    debug=app_settings.debug,
    root_path=app_settings.app_root_path,
    lifespan=lifespan,
  )
  app.add_middleware(RequestContextMiddleware)
  register_exception_handlers(app)

  app.include_router(api_router)
  return app


app = create_app()
