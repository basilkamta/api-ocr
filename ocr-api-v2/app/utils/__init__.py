# =============================================================================
# EXTRACTEURS SPÉCIALISÉS
# =============================================================================

# app/extractors/metadata_extractor.py

# =============================================================================
# UTILITAIRES IMAGES
# =============================================================================

# app/utils/image_utils.py

# =============================================================================
# ROUTES MISES À JOUR
# =============================================================================

# app/main.py (version complète)
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import tempfile
import time
from pathlib import Path
import numpy as np

from .config import settings
from .models import (
    OCRRequest, OCRResponse, OCREngine, ExtractionMode,
    EnginesListResponse, EngineResult
)
from .services.ocr_factory import get_ocr_factory, OCRFactory
from .extractors.metadata_extractor import MetadataExtractor
from .utils.image_utils import ImagePreprocessor

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Création de l'application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API OCR Multi-Moteurs (PaddleOCR, EasyOCR, Kraken)"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instances globales
extractor = MetadataExtractor()
preprocessor = ImagePreprocessor()

# Dépendance API Key
async def verify_api_key(api_key: str = Query(..., alias="api_key")):
    if api_key != settings.api_key:
        raise HTTPException(401, "Clé API invalide")
    return api_key

# =============================================================================
# ROUTES SANTÉ
# =============================================================================

@app.get("/")
async def root():
    return {
        "message": f"Bienvenue sur {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "engines": settings.available_engines
    }

@app.get("/health")
async def health_check():
    """Santé globale de l'API"""
    factory = get_ocr_factory()
    available_engines = factory.get_available_engines()
    
    return {
        "status": "healthy" if available_engines else "degraded",
        "version": settings.app_version,
        "engines": {
            "available": available_engines,
            "default": settings.default_engine,
            "fallback_enabled": settings.enable_fallback
        }
    }

@app.get("/health/detailed")
async def detailed_health():
    """Santé détaillée avec infos moteurs"""
    factory = get_ocr_factory()
    engines_info = factory.get_engines_info()
    
    return {
        "status": "healthy",
        "version": settings.app_version,
        "engines": [info.dict() for info in engines_info],
        "config": {
            "fallback_enabled": settings.enable_fallback,
            "confidence_threshold": settings.confidence_threshold,
            "preprocessing": settings.enable_preprocessing
        }
    }

# =============================================================================
# ROUTES MOTEURS
# =============================================================================

@app.get("/api/v1/engines", response_model=EnginesListResponse)
async def list_engines(api_key: str = Depends(verify_api_key)):
    """Liste tous les moteurs OCR disponibles"""
    factory = get_ocr_factory()
    engines_info = factory.get_engines_info()
    
    return EnginesListResponse(
        engines=engines_info,
        default_engine=settings.default_engine,
        fallback_enabled=settings.enable_fallback
    )

@app.get("/api/v1/engines/{engine_name}")
async def get_engine_info(
    engine_name: str,
    api_key: str = Depends(verify_api_key)
):
    """Détails d'un moteur spécifique"""
    factory = get_ocr_factory()
    engine = factory.get_engine(engine_name)
    
    if not engine:
        raise HTTPException(404, f"Moteur {engine_name} non trouvé")
    
    return engine.get_info()

@app.post("/api/v1/engines/{engine_name}/test")
async def test_engine(
    engine_name: str,
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """Teste un moteur spécifique sur un document"""
    factory = get_ocr_factory()
    engine = factory.get_engine(engine_name)
    
    if not engine:
        raise HTTPException(404, f"Moteur {engine_name} non trouvé")
    
    # Chargement fichier
    content = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    
    try:
        # Conversion en image
        import cv2
        image = cv2.imread(str(tmp_path))
        
        if image is None:
            raise HTTPException(400, "Impossible de lire l'image")
        
        # Test extraction
        start_time = time.time()
        text, confidence = await engine.extract_text(image)
        processing_time = time.time() - start_time
        
        return {
            "engine": engine_name,
            "success": True,
            "text": text[:500],
            "confidence": confidence,
            "processing_time": processing_time
        }
        
    finally:
        tmp_path.unlink()

# =============================================================================
# ROUTES OCR PRINCIPALES
# =============================================================================

@app.post("/api/v1/ocr/extract", response_model=OCRResponse)
async def extract_simple(
    file: UploadFile = File(...),
    engine: OCREngine = Query(OCREngine.AUTO, description="Moteur OCR"),
    extract_mandat: bool = Query(True),
    extract_bordereau: bool = Query(True),
    extract_exercice: bool = Query(True),
    api_key: str = Depends(verify_api_key),
    factory: OCRFactory = Depends(get_ocr_factory)
):
    """
    Extraction OCR simple
    
    - **file**: Document PDF ou image
    - **engine**: Moteur à utiliser (auto, paddleocr, easyocr, kraken)
    - **extract_mandat**: Extraire le numéro de mandat
    - **extract_bordereau**: Extraire le numéro de bordereau
    - **extract_exercice**: Extraire l'exercice fiscal
    """
    start_time = time.time()
    
    # Validation fichier
    if not file.filename:
        raise HTTPException(400, "Nom de fichier manquant")
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ['.pdf', '.png', '.jpg', '.jpeg']:
        raise HTTPException(400, "Format non supporté")
    
    content = await file.read()
    if len(content) > settings.max_file_size:
        raise HTTPException(413, "Fichier trop volumineux")
    
    # Sauvegarde temporaire
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    
    try:
        # Conversion en image
        if file_ext == '.pdf':
            image = preprocessor.pdf_to_image(str(tmp_path))
        else:
            import cv2
            image = cv2.imread(str(tmp_path))
        
        if image is None:
            raise HTTPException(400, "Impossible de lire le fichier")
        
        # Preprocessing
        processed_image = preprocessor.preprocess(image, mode="standard")
        
        # Extraction OCR avec fallback
        text, confidence, engines_used = await factory.extract_with_fallback(
            processed_image,
            preferred_engine=engine.value,
            enable_fallback=settings.enable_fallback
        )
        
        # Extraction métadonnées
        metadata = extractor.extract_all(text)
        
        # Construction réponse
        response = OCRResponse(
            success=bool(metadata['mandat'] or metadata['bordereau']),
            processing_time=time.time() - start_time,
            primary_engine=engines_used[0].engine if engines_used else "unknown",
            engines_used=engines_used,
            fallback_triggered=len(engines_used) > 1,
            mandat=metadata['mandat'] if extract_mandat else None,
            bordereau=metadata['bordereau'] if extract_bordereau else None,
            exercice=metadata['exercice'] if extract_exercice else None,
            raw_text=text[:500],
            confidence_score=confidence,
            preprocessing_applied=["standard"]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur extraction {file.filename}: {e}")
        raise HTTPException(500, f"Erreur: {str(e)}")
    
    finally:
        tmp_path.unlink()

@app.post("/api/v1/ocr/extract/advanced", response_model=OCRResponse)
async def extract_advanced(
    file: UploadFile = File(...),
    request: OCRRequest = Depends(),
    api_key: str = Depends(verify_api_key),
    factory: OCRFactory = Depends(get_ocr_factory)
):
    """
    Extraction OCR avancée avec toutes les options
    
    Permet de configurer finement:
    - Moteur OCR et fallback
    - Extraction de données spécifiques
    - Mode de traitement (fast, standard, accurate)
    - Seuil de confiance
    """
    start_time = time.time()
    
    # Validation fichier
    if not file.filename:
        raise HTTPException(400, "Nom de fichier manquant")
    
    content = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    
    try:
        # Conversion image
        file_ext = Path(file.filename).suffix.lower()
        if file_ext == '.pdf':
            image = preprocessor.pdf_to_image(str(tmp_path))
        else:
            import cv2
            image = cv2.imread(str(tmp_path))
        
        # Preprocessing selon le mode
        processed_image = preprocessor.preprocess(image, mode=request.mode.value)
        
        # Extraction OCR
        text, confidence, engines_used = await factory.extract_with_fallback(
            processed_image,
            preferred_engine=request.engine.value,
            enable_fallback=request.enable_fallback,
            fallback_engines=request.fallback_engines
        )
        
        # Obtenir extractions avec coordonnées du meilleur moteur
        if engines_used and engines_used[0].success:
            best_engine = factory.get_engine(engines_used[0].engine)
            coords = await best_engine.extract_with_coordinates(processed_image)
        else:
            coords = None
        
        # Extraction métadonnées
        metadata = extractor.extract_all(text, coords)
        
        # Construction réponse complète
        response = OCRResponse(
            success=bool(metadata['mandat'] or metadata['bordereau']),
            processing_time=time.time() - start_time,
            primary_engine=engines_used[0].engine if engines_used else "unknown",
            engines_used=engines_used,
            fallback_triggered=len(engines_used) > 1,
            mandat=metadata['mandat'] if request.extract_mandat else None,
            bordereau=metadata['bordereau'] if request.extract_bordereau else None,
            exercice=metadata['exercice'] if request.extract_exercice else None,
            dates=metadata['dates'] if request.extract_dates else None,
            amounts=metadata['amounts'] if request.extract_amounts else None,
            raw_text=text[:1000],
            confidence_score=confidence,
            preprocessing_applied=[request.mode.value]
        )
        
        return response
        
    finally:
        tmp_path.unlink()

# =============================================================================
# ROUTES EXTRACTION SPÉCIALISÉES
# =============================================================================

@app.post("/api/v1/extract/mandat")
async def extract_mandat_only(
    file: UploadFile = File(...),
    engine: OCREngine = Query(OCREngine.AUTO),
    api_key: str = Depends(verify_api_key)
):
    """Extrait uniquement le numéro de mandat"""
    # Utiliser extract_simple avec filtres
    result = await extract_simple(
        file=file,
        engine=engine,
        extract_mandat=True,
        extract_bordereau=False,
        extract_exercice=False,
        api_key=api_key,
        factory=get_ocr_factory()
    )
    
    return {
        "success": result.success,
        "mandat": result.mandat,
        "confidence": result.confidence_score,
        "processing_time": result.processing_time
    }

@app.post("/api/v1/extract/bordereau")
async def extract_bordereau_only(
    file: UploadFile = File(...),
    engine: OCREngine = Query(OCREngine.AUTO),
    api_key: str = Depends(verify_api_key)
):
    """Extrait uniquement le numéro de bordereau"""
    result = await extract_simple(
        file=file,
        engine=engine,
        extract_mandat=False,
        extract_bordereau=True,
        extract_exercice=False,
        api_key=api_key,
        factory=get_ocr_factory()
    )
    
    return {
        "success": result.success,
        "bordereau": result.bordereau,
        "confidence": result.confidence_score,
        "processing_time": result.processing_time
    }

# =============================================================================
# Point d'entrée
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)