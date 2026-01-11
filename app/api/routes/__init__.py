"""API routes package."""

from fastapi import APIRouter

from app.api.routes.webhook import router as webhook_router

router = APIRouter()
router.include_router(webhook_router)
