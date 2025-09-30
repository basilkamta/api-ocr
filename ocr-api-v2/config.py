from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # API
    app_name: str = "API OCR MVP"
    app_version: str = "1.0.0-mvp"
    api_key: str = os.getenv("API_KEY", "test-api-key")
    
    # OCR
    ocr_engine: str = "paddleocr"  # paddleocr par défaut
    use_gpu: bool = False  # Mettre True si GPU disponible
    default_lang: str = "fr"
    det_db_thresh: float = 0.3
    det_db_box_thresh: float = 0.5
    
    # Fichiers
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    upload_dir: str = "/tmp/uploads"
    
    # Performance
    enable_cache: bool = False  # Désactivé pour MVP
    
    class Config:
        env_file = ".env"

settings = Settings()