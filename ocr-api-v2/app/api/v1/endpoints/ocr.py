from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query, Body
from typing import Optional
import tempfile
from pathlib import Path
import time

from ....schemas.ocr import OCRRequest, OCRResponse, ExtractionMode, OCREngine
from ....services.ocr_factory import get_ocr_factory, OCRFactory
from ....extractors.metadata_extractor import MetadataExtractor
from ....utils.image_utils import ImagePreprocessor
from ....dependencies import get_current_api_key, get_extractor, get_preprocessor
from ....core.metrics import track_request
from ....config import get_settings

router = APIRouter()
settings = get_settings()

@router.post("/extract", response_model=OCRResponse, tags=["OCR"])
@track_request("/api/v1/ocr/extract")
async def extract_simple(
    file: UploadFile = File(...),
    engine: OCREngine = Query(OCREngine.AUTO),
    extract_mandat: bool = Query(True),
    extract_bordereau: bool = Query(True),
    extract_exercice: bool = Query(True),
    api_key: str = Depends(get_current_api_key),
    factory: OCRFactory = Depends(get_ocr_factory),
    extractor: MetadataExtractor = Depends(get_extractor),
    preprocessor: ImagePreprocessor = Depends(get_preprocessor)
):
    """
    Extraction OCR simple avec paramètres de base
    
    - **file**: Document PDF ou image (PNG, JPG, JPEG)
    - **engine**: Moteur OCR à utiliser (auto, paddleocr, easyocr, kraken)
    - **extract_mandat**: Extraire le numéro de mandat
    - **extract_bordereau**: Extraire le numéro de bordereau
    - **extract_exercice**: Extraire l'exercice fiscal
    
    Retourne les métadonnées extraites avec scores de confiance.
    """
    start_time = time.time()
    
    # Validation du fichier
    if not file.filename:
        raise HTTPException(400, "Nom de fichier manquant")
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff']:
        raise HTTPException(400, f"Format non supporté: {file_ext}")
    
    content = await file.read()
    if len(content) > settings.max_file_size:
        raise HTTPException(413, "Fichier trop volumineux")
    
    # Traitement
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
        
        # Preprocessing
        processed_image = preprocessor.preprocess(image, mode="standard")
        
        # Extraction OCR
        text, confidence, engines_used = await factory.extract_with_fallback(
            processed_image,
            preferred_engine=engine.value,
            enable_fallback=settings.enable_fallback
        )
        
        # Extraction métadonnées
        metadata = extractor.extract_all(text)
        
        # Construction réponse
        return OCRResponse(
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
    
    finally:
        tmp_path.unlink()

@router.post("/extract/advanced", response_model=OCRResponse, tags=["OCR"])
@track_request("/api/v1/ocr/extract/advanced")
async def extract_advanced(
    file: UploadFile = File(...),
    request: OCRRequest = Body(...),
    api_key: str = Depends(get_current_api_key),
    factory: OCRFactory = Depends(get_ocr_factory),
    extractor: MetadataExtractor = Depends(get_extractor),
    preprocessor: ImagePreprocessor = Depends(get_preprocessor)
):
    """
    Extraction OCR avancée avec configuration complète
    
    Permet de configurer:
    - Moteur OCR et ordre de fallback
    - Données à extraire (mandat, bordereau, dates, montants)
    - Mode de traitement (fast, standard, accurate)
    - Seuils de confiance personnalisés
    - Options de preprocessing
    """
    # Implémentation similaire à extract_simple mais avec plus d'options
    # ... (voir code complet dans l'artifact précédent)
    pass

@router.post("/batch", tags=["OCR"])
async def batch_extract(
    files: List[UploadFile] = File(...),
    api_key: str = Depends(get_current_api_key)
):
    """
    Extraction batch (plusieurs fichiers)
    
    Soumet un lot de fichiers pour traitement asynchrone.
    Retourne un batch_id pour suivre l'avancement.
    """
    # À implémenter avec Celery
    return {"message": "Batch processing - à implémenter avec Celery"}

@router.get("/batch/{batch_id}", tags=["OCR"])
async def get_batch_status(
    batch_id: str,
    api_key: str = Depends(get_current_api_key)
):
    """
    Statut d'un traitement batch
    """
    # À implémenter
    return {"batch_id": batch_id, "status": "pending"}

@router.get("/result/{result_id}", tags=["OCR"])
async def get_result(
    result_id: str,
    api_key: str = Depends(get_current_api_key)
):
    """
    Récupère un résultat OCR par son ID
    """
    # À implémenter avec DB
    return {"result_id": result_id}

@router.delete("/result/{result_id}", tags=["OCR"])
async def delete_result(
    result_id: str,
    api_key: str = Depends(get_current_api_key)
):
    """
    Supprime un résultat OCR
    """
    # À implémenter avec DB
    return {"message": "Result deleted"}

@router.get("/results", tags=["OCR"])
async def list_results(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    api_key: str = Depends(get_current_api_key)
):
    """
    Liste des résultats OCR avec pagination
    """