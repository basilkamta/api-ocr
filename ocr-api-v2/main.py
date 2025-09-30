from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import tempfile
import shutil
from pathlib import Path
import cv2

from .config import settings
from .models import OCRRequest, OCRResponse, HealthResponse
from .ocr_service import get_ocr_service, OCRService, PADDLE_AVAILABLE

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
    description="MVP API OCR avec PaddleOCR"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dépendance pour l'API Key (simple pour MVP)
async def verify_api_key(api_key: str = Query(..., alias="api_key")):
    if api_key != settings.api_key:
        raise HTTPException(401, "Clé API invalide")
    return api_key

# =============================================================================
# ROUTES
# =============================================================================

@app.get("/")
async def root():
    return {
        "message": f"Bienvenue sur {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Vérification de santé de l'API"""
    
    # Vérifier si GPU disponible
    gpu_available = False
    try:
        import paddle
        gpu_available = paddle.is_compiled_with_cuda()
    except:
        pass
    
    return HealthResponse(
        status="healthy" if PADDLE_AVAILABLE else "degraded",
        version=settings.app_version,
        engine="paddleocr" if PADDLE_AVAILABLE else "none",
        gpu_available=gpu_available
    )

@app.post("/ocr/extract", response_model=OCRResponse)
async def extract_document(
    file: UploadFile = File(...),
    extract_mandat: bool = Query(True),
    extract_bordereau: bool = Query(True),
    extract_exercice: bool = Query(True),
    api_key: str = Depends(verify_api_key),
    ocr_service: OCRService = Depends(get_ocr_service)
):
    """
    Extraction OCR depuis un document PDF ou image
    
    - **file**: Fichier PDF ou image (PNG, JPG)
    - **extract_mandat**: Extraire le numéro de mandat
    - **extract_bordereau**: Extraire le numéro de bordereau
    - **extract_exercice**: Extraire l'exercice fiscal
    """
    
    # Validation du fichier
    if not file.filename:
        raise HTTPException(400, "Nom de fichier manquant")
    
    allowed_extensions = ['.pdf', '.png', '.jpg', '.jpeg']
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(400, f"Format non supporté. Formats acceptés: {allowed_extensions}")
    
    # Vérification de la taille
    content = await file.read()
    if len(content) > settings.max_file_size:
        raise HTTPException(413, "Fichier trop volumineux")
    
    # Sauvegarde temporaire
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        tmp_file.write(content)
        tmp_path = Path(tmp_file.name)
    
    try:
        # Si PDF, convertir en image
        if file_ext == '.pdf':
            image_path = await _pdf_to_image(tmp_path)
        else:
            image_path = tmp_path
        
        # Paramètres d'extraction
        params = OCRRequest(
            extract_mandat=extract_mandat,
            extract_bordereau=extract_bordereau,
            extract_exercice=extract_exercice
        )
        
        # Traitement OCR
        result = await ocr_service.process_document(image_path, params)
        
        return result
        
    except Exception as e:
        logger.error(f"Erreur traitement {file.filename}: {e}")
        raise HTTPException(500, f"Erreur traitement: {str(e)}")
    
    finally:
        # Nettoyage
        try:
            tmp_path.unlink()
            if file_ext == '.pdf' and image_path != tmp_path:
                image_path.unlink()
        except:
            pass

async def _pdf_to_image(pdf_path: Path) -> Path:
    """Convertit un PDF en image"""
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open(str(pdf_path))
        page = doc[0]
        
        # Conversion en image
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # DPI ~144
        
        # Sauvegarde temporaire
        image_path = pdf_path.with_suffix('.png')
        pix.save(str(image_path))
        
        doc.close()
        return image_path
        
    except Exception as e:
        logger.error(f"Erreur conversion PDF: {e}")
        raise

# =============================================================================
# Point d'entrée
# =============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)