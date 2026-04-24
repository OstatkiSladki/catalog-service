from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api import api_router
from src.config.logging import configure_logging
from src.config.settings import Settings, get_settings
from src.db.session import DatabaseSessionManager
from src.grpc.clients import OrderQueryClient, VenueDirectoryClient
from src.grpc import start_grpc_server, stop_grpc_server
from src.middleware.error_handler import register_exception_handlers
from src.middleware.request_context import RequestContextMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
  app_settings = settings or get_settings()
  configure_logging(app_settings)

  @asynccontextmanager
  async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    session_manager = DatabaseSessionManager.from_settings(app_settings)
    app.state.session_manager = session_manager
    venue_directory_client = VenueDirectoryClient()
    order_query_client = OrderQueryClient()
    app.state.venue_directory_client = venue_directory_client
    app.state.order_query_client = order_query_client
    if app_settings.grpc_startup_checks_enabled:
      await venue_directory_client.wait_until_serving()
      await order_query_client.wait_until_serving()
    grpc_server, grpc_health = await start_grpc_server(session_manager)
    app.state.grpc_server = grpc_server
    app.state.grpc_health = grpc_health
    try:
      yield
    finally:
      await stop_grpc_server(grpc_server, grpc_health)
      await venue_directory_client.close()
      await order_query_client.close()
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
