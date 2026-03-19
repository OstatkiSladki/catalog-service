from __future__ import annotations

from fastapi import APIRouter, Request

from src.schemas.common import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
  return HealthResponse(status="ok", version=request.app.version)


@router.get("/ready", response_model=HealthResponse)
async def ready(request: Request) -> HealthResponse:
  session_manager = request.app.state.session_manager
  healthy = await session_manager.healthcheck()
  status_value = "ok" if healthy else "degraded"
  return HealthResponse(status=status_value, version=request.app.version)
