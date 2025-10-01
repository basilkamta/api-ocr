from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache
import os
from pathlib import Path

class Settings(BaseSettings):
    """Configuration globale de l'application"""
    
    # Application
    app_name: str = "API OCR Multi-Moteurs FEICOM"
    app_version: str = "2.0.0"
    debug: bool = False
    
    # API
    api_v1_prefix: str = "/api/v1"
    
    # Serveur
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # Sécurité
    secret_key: str = os.getenv("SECRET_KEY", "CHANGE-ME-IN-PRODUCTION")
    api_key: str = os.getenv("API_KEY", "test-api-key")
    allowed_origins: List[str] = ["*"]
    
    # OCR Engines
    available_engines: List[str] = ["paddleocr", "easyocr", "kraken"]
    default_engine: str = "paddleocr"
    enable_fallback: bool = True
    fallback_order: List[str] = ["paddleocr", "easyocr", "kraken"]
    
    # PaddleOCR
    paddle_use_gpu: bool = False
    paddle_lang: str = "fr"
    paddle_det_db_thresh: float = 0.3
    paddle_det_db_box_thresh: float = 0.5
    
    # EasyOCR
    easy_use_gpu: bool = False
    easy_languages: List[str] = ["fr", "en"]
    easy_download_enabled: bool = True
    
    # Kraken
    kraken_model: str = "/app/models/fr_best.mlmodel"  # ✅ Chemin absolu
    kraken_device: str = "cpu"
    models_dir: str = "/app/models"  # ✅ Nouveau: répertoire des modèles
    
    # Preprocessing
    enable_preprocessing: bool = True
    target_dpi: int = 300
    
    # Performance
    confidence_threshold: float = 0.6
    max_fallback_attempts: int = 3
    
    # Fichiers
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    upload_dir: str = "/tmp/uploads"
    temp_dir: str = "/tmp/ocr_temp"
    
    # Base de données
    database_url: Optional[str] = None
    db_pool_size: int = 10
    db_max_overflow: int = 20
    
    # Cache
    redis_url: Optional[str] = None
    cache_enabled: bool = False
    cache_ttl: int = 3600
    
    # Celery
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None
    
    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Récupère les paramètres (cached)"""
    return Settings()

settings = get_settings()


# ✅ Créer le répertoire des modèles au démarrage
Path(settings.models_dir).mkdir(parents=True, exist_ok=True)