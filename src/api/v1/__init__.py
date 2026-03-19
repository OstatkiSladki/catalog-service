from fastapi import APIRouter

from src.api.v1.categories import router as categories_router
from src.api.v1.health import router as health_router
from src.api.v1.offers import router as offers_router
from src.api.v1.products import router as products_router
from src.api.v1.reviews import router as reviews_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(health_router, tags=["Health"])
v1_router.include_router(categories_router, tags=["Categories"])
v1_router.include_router(products_router, tags=["Products"])
v1_router.include_router(offers_router, tags=["Offers"])
v1_router.include_router(reviews_router, tags=["Reviews"])
