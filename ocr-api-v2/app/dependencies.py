from fastapi import Depends
from typing import Generator
from sqlalchemy.orm import Session

from .core.security import get_api_key
from .services.ocr_factory import get_ocr_factory, OCRFactory
from .extractors.metadata_extractor import MetadataExtractor
from .utils.image_utils import ImagePreprocessor

# Dépendances réutilisables

async def get_current_api_key(api_key: str = Depends(get_api_key)) -> str:
    """Dépendance pour récupérer la clé API validée"""
    return api_key

def get_ocr_factory_dep() -> OCRFactory:
    """Dépendance pour le factory OCR"""
    return get_ocr_factory()

def get_extractor() -> MetadataExtractor:
    """Dépendance pour l'extracteur de métadonnées"""
    if not hasattr(get_extractor, "_instance"):
        get_extractor._instance = MetadataExtractor()
    return get_extractor._instance

def get_preprocessor() -> ImagePreprocessor:
    """Dépendance pour le preprocessor d'images"""
    if not hasattr(get_preprocessor, "_instance"):
        get_preprocessor._instance = ImagePreprocessor()
    return get_preprocessor._instance

# Base de données (to Implement later if needed)
# def get_db() -> Generator[Session, None, None]:
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
