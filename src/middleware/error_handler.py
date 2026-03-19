from __future__ import annotations

from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.schemas.common import ErrorResponse


def register_exception_handlers(app: FastAPI) -> None:
  @app.exception_handler(Exception)
  async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    response = ErrorResponse(
      code="INTERNAL_ERROR",
      message="Internal server error",
      details={"error": str(exc)},
      timestamp=datetime.now(UTC),
      request_id=getattr(request.state, "request_id", "unknown"),
      trace_id=None,
    )
    return JSONResponse(status_code=500, content=response.model_dump(mode="json"))
