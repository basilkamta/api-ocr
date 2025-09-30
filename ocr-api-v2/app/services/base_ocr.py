from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np

from app.schemas.engine import EngineInfo

class BaseOCRService(ABC):
    """Classe abstraite pour les services OCR"""
    
    def __init__(self):
        self.engine_name = "base"
        self.is_initialized = False
        self.supports_gpu = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialise le moteur OCR"""
        pass
    
    @abstractmethod
    async def extract_text(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Extrait le texte d'une image
        Returns: (texte, confiance moyenne)
        """
        pass
    
    @abstractmethod
    async def extract_with_coordinates(self, image: np.ndarray) -> List[Dict]:
        """
        Extrait le texte avec coordonnées
        Returns: Liste de {text, confidence, bbox}
        """
        pass
    
    async def cleanup(self):
        """Nettoyage des ressources"""
        pass
    
    def get_info(self) -> EngineInfo:
        """Retourne les infos du moteur"""
        return EngineInfo(
            name=self.engine_name,
            available=self.is_initialized,
            version="unknown",
            supports_gpu=self.supports_gpu,
            languages=[]
        )
