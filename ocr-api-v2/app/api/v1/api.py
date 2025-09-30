from fastapi import APIRouter

from .endpoints import health, ocr, engines, documents, validation, batch, admin

api_router = APIRouter()

# Inclusion de toutes les routes
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(ocr.router, prefix="/ocr", tags=["OCR"])
api_router.include_router(engines.router, prefix="/engines", tags=["Engines"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(validation.router, prefix="/validation", tags=["Validation"])
api_router.include_router(batch.router, prefix="/batch", tags=["Batch"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])