from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from typing import List

from ....schemas.engine import EngineInfo, EnginesListResponse, EngineTestResponse
from ....schemas.responses import StandardResponse
from ....services.ocr_factory import get_ocr_factory, OCRFactory
from ....dependencies import get_current_api_key
from ....config import get_settings

router = APIRouter()
settings = get_settings()

@router.get("/", response_model=EnginesListResponse, tags=["Engines"])
async def list_engines(
    api_key: str = Depends(get_current_api_key),
    factory: OCRFactory = Depends(get_ocr_factory)
):
    """
    Liste tous les moteurs OCR disponibles
    """
    engines_info = factory.get_engines_info()
    
    return EnginesListResponse(
        engines=engines_info,
        default_engine=settings.default_engine,
        fallback_enabled=settings.enable_fallback
    )

@router.get("/{engine_name}", response_model=EngineInfo, tags=["Engines"])
async def get_engine_info(
    engine_name: str,
    api_key: str = Depends(get_current_api_key),
    factory: OCRFactory = Depends(get_ocr_factory)
):
    """
    Détails d'un moteur OCR spécifique
    """
    engine = factory.get_engine(engine_name)
    
    if not engine:
        raise HTTPException(404, f"Moteur '{engine_name}' non trouvé")
    
    return engine.get_info()

@router.get("/{engine_name}/status", tags=["Engines"])
async def get_engine_status(
    engine_name: str,
    api_key: str = Depends(get_current_api_key),
    factory: OCRFactory = Depends(get_ocr_factory)
):
    """
    Statut d'un moteur OCR
    """
    engine = factory.get_engine(engine_name)
    
    if not engine:
        raise HTTPException(404, f"Moteur '{engine_name}' non trouvé")
    
    return {
        "engine": engine_name,
        "available": engine.is_initialized,
        "supports_gpu": engine.supports_gpu
    }

@router.post("/{engine_name}/test", response_model=EngineTestResponse, tags=["Engines"])
async def test_engine(
    engine_name: str,
    file: UploadFile = File(...),
    api_key: str = Depends(get_current_api_key),
    factory: OCRFactory = Depends(get_ocr_factory)
):
    """
    Teste un moteur sur un document
    """
    engine = factory.get_engine(engine_name)
    
    if not engine:
        raise HTTPException(404, f"Moteur '{engine_name}' non trouvé")
    
    # Implémentation du test...
    # (Code d'extraction simplifié)
    
    return EngineTestResponse(
        engine=engine_name,
        success=True,
        message=f"Test du moteur {engine_name} réussi"
    )

@router.get("/compare", tags=["Engines"])
async def compare_engines(
    api_key: str = Depends(get_current_api_key)
):
    """
    Compare les performances des moteurs
    """
    # Implémentation de la comparaison
    return {"message": "Endpoint de comparaison - à implémenter"}

@router.post("/benchmark", tags=["Engines"])
async def benchmark_engines(
    files: List[UploadFile] = File(...),
    api_key: str = Depends(get_current_api_key)
):
    """
    Benchmark tous les moteurs sur plusieurs fichiers
    """
    # Implémentation du benchmark
    return {"message": "Endpoint de benchmark - à implémenter"}
