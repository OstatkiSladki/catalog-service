from __future__ import annotations

from fastapi import HTTPException, status


def missing_required_identity_headers() -> HTTPException:
  return HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Missing required identity headers",
  )


def identity_required() -> HTTPException:
  return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identity required")


def admin_role_required() -> HTTPException:
  return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")


def staff_or_admin_role_required() -> HTTPException:
  return HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Staff or admin role required",
  )


def own_reviews_filter_only() -> HTTPException:
  return HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="You can only filter your own reviews",
  )


def category_not_found() -> HTTPException:
  return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")


def product_not_found() -> HTTPException:
  return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")


def offer_not_found() -> HTTPException:
  return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")


def review_not_found() -> HTTPException:
  return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")


def slug_already_exists() -> HTTPException:
  return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")


def invalid_category_relation() -> HTTPException:
  return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid category relation")


def invalid_offer_items() -> HTTPException:
  return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid offer items")


def review_conflict() -> HTTPException:
  return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Review conflict")


def venue_or_product_not_found() -> HTTPException:
  return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue or product not found")


def bad_request(detail: str) -> HTTPException:
  return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def forbidden(detail: str) -> HTTPException:
  return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def conflict(detail: str) -> HTTPException:
  return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
