from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api import exceptions
from src.repositories.category_repository import CategoryRepository
from src.repositories.offer_repository import OfferRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.review_repository import ReviewRepository


class IdentityContext(BaseModel):
  user_id: str
  user_role: str
  request_id: str
  user_venue_id: int | None = None


async def get_identity_context(
  x_user_id: Annotated[str | None, Header(alias="X-User-ID")] = None,
  x_user_role: Annotated[str | None, Header(alias="X-User-Role")] = None,
  x_request_id: Annotated[str | None, Header(alias="X-Request-ID")] = None,
  x_user_venue_id: Annotated[int | None, Header(alias="X-User-Venue-ID")] = None,
) -> IdentityContext:
  if not x_user_id or not x_request_id:
    raise exceptions.missing_required_identity_headers()
  return IdentityContext(
    user_id=x_user_id,
    user_role=x_user_role or "user",
    request_id=x_request_id,
    user_venue_id=x_user_venue_id,
  )


async def require_admin(
  identity: Annotated[IdentityContext, Depends(get_identity_context)],
) -> IdentityContext:
  if identity.user_role != "admin":
    raise exceptions.admin_role_required()
  return identity


async def require_staff_or_admin(
  identity: Annotated[IdentityContext, Depends(get_identity_context)],
) -> IdentityContext:
  if identity.user_role not in {"staff", "admin"}:
    raise exceptions.staff_or_admin_role_required()
  return identity


async def get_optional_identity_context(
  x_user_id: Annotated[str | None, Header(alias="X-User-ID")] = None,
  x_user_role: Annotated[str | None, Header(alias="X-User-Role")] = None,
  x_request_id: Annotated[str | None, Header(alias="X-Request-ID")] = None,
  x_user_venue_id: Annotated[int | None, Header(alias="X-User-Venue-ID")] = None,
) -> IdentityContext | None:
  if all(value is None for value in (x_user_id, x_user_role, x_request_id, x_user_venue_id)):
    return None
  if not x_user_id or not x_request_id:
    raise exceptions.missing_required_identity_headers()
  return IdentityContext(
    user_id=x_user_id,
    user_role=x_user_role or "user",
    request_id=x_request_id,
    user_venue_id=x_user_venue_id,
  )


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
  session_manager = request.app.state.session_manager
  async for session in session_manager.session():
    yield session


DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def get_category_repository(session: DbSession) -> CategoryRepository:
  return CategoryRepository(session)


def get_product_repository(session: DbSession) -> ProductRepository:
  return ProductRepository(session)


def get_offer_repository(session: DbSession) -> OfferRepository:
  return OfferRepository(session)


def get_review_repository(session: DbSession) -> ReviewRepository:
  return ReviewRepository(session)
