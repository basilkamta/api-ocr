from fastapi import APIRouter, Depends
from typing import Dict, List
import platform
import psutil
from datetime import datetime

from ....schemas.response import HealthResponse, DetailedHealthResponse
from ....services.ocr_factory import get_ocr_factory
from ....config import get_settings

router = APIRouter()
settings = get_settings()

@router.get("/", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Vérification basique de santé de l'API
    """
    factory = get_ocr_factory()
    available_engines = factory.get_available_engines()
    
    return HealthResponse(
        status="healthy" if available_engines else "degraded",
        version=settings.app_version,
        timestamp=datetime.utcnow()
    )

@router.get("/detailed", response_model=DetailedHealthResponse, tags=["Health"])
async def detailed_health():
    """
    Vérification détaillée avec métriques système
    """
    factory = get_ocr_factory()
    engines_info = factory.get_engines_info()
    
    # Métriques système
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    
    return DetailedHealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        engines=[info.dict() for info in engines_info],
        system={
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024**3), 2)
        },
        config={
            "fallback_enabled": settings.enable_fallback,
            "confidence_threshold": settings.confidence_threshold,
            "preprocessing": settings.enable_preprocessing
        }
    )

@router.get("/live", tags=["Health"])
async def liveness_probe():
    """
    Liveness probe pour Kubernetes
    """
    return {"status": "alive"}

@router.get("/ready", tags=["Health"])
async def readiness_probe():
    """
    Readiness probe pour Kubernetes
    """
    factory = get_ocr_factory()
    available_engines = factory.get_available_engines()
    
    if not available_engines:
        return {"status": "not_ready", "reason": "no_engines_available"}, 503
    
    return {"status": "ready", "engines": available_engines}