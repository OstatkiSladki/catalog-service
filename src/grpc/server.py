from __future__ import annotations

from grpc_health.v1 import health, health_pb2, health_pb2_grpc

import grpc
from src.config.settings import get_settings
from src.db.session import DatabaseSessionManager
from src.grpc.generated import catalog_inventory_pb2_grpc
from src.grpc.service import CatalogInventoryGrpcService

_SERVICE_NAME = "ostatki.grpc.v1.CatalogInventoryService"


async def start_grpc_server(
  session_manager: DatabaseSessionManager,
) -> tuple[grpc.aio.Server, health.HealthServicer]:
  settings = get_settings()
  server = grpc.aio.server()
  health_servicer = health.aio.HealthServicer()

  catalog_inventory_pb2_grpc.add_CatalogInventoryServiceServicer_to_server(
    CatalogInventoryGrpcService(session_manager),
    server,
  )
  health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)

  server.add_insecure_port(f"{settings.grpc_host}:{settings.grpc_port}")
  await server.start()

  await health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)
  await health_servicer.set(_SERVICE_NAME, health_pb2.HealthCheckResponse.SERVING)
  return server, health_servicer


async def stop_grpc_server(
  server: grpc.aio.Server,
  health_servicer: health.HealthServicer,
) -> None:
  await health_servicer.set(_SERVICE_NAME, health_pb2.HealthCheckResponse.NOT_SERVING)
  await health_servicer.set("", health_pb2.HealthCheckResponse.NOT_SERVING)
  await server.stop(grace=5)
