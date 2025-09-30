"""
Classe de base abstraite pour tous les extracteurs
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict


class BaseExtractor(ABC):
    """
    Classe abstraite pour les extracteurs de métadonnées
    
    Tous les extracteurs spécialisés doivent hériter de cette classe
    """
    
    @abstractmethod
    def extract(self, text: str, **kwargs) -> Any:
        """
        Extrait les données depuis le texte
        
        Args:
            text: Texte OCR à analyser
            **kwargs: Arguments additionnels (coordinates, context, etc.)
        
        Returns:
            Données extraites (format dépend de l'extracteur)
        """
        pass
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """
        Valide les données extraites
        
        Args:
            data: Données à valider
        
        Returns:
            True si valide, False sinon
        """
        pass
    
    def preprocess_text(self, text: str) -> str:
        """
        Prétraitement du texte avant extraction
        
        Peut être surchargé par les classes enfants
        """
        if not text:
            return ""
        
        # Nettoyage basique
        from ..utils.text_utils import normalize_whitespace, clean_ocr_artifacts
        
        text = clean_ocr_artifacts(text)
        text = normalize_whitespace(text)
        
        return text
    
    def extract_with_confidence(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Extrait avec score de confiance
        
        Returns:
            {data: Any, confidence: float}
        """
        data = self.extract(text, **kwargs)
        
        if data is None:
            return {'data': None, 'confidence': 0.0}
        
        confidence = self.calculate_confidence(data, text)
        
        return {
            'data': data,
            'confidence': confidence
        }
    
    def calculate_confidence(self, data: Any, text: str) -> float:
        """
        Calcule un score de confiance pour les données extraites
        
        Peut être surchargé par les classes enfants
        
        Returns:
            Score entre 0.0 et 1.0
        """
        if data is None:
            return 0.0
        
        # Confiance par défaut si données trouvées
        return 0.85
    
    def get_extraction_context(self, match_text: str, full_text: str, window: int = 100) -> str:
        """
        Récupère le contexte autour d'une correspondance
        
        Args:
            match_text: Texte trouvé
            full_text: Texte complet
            window: Nombre de caractères de contexte avant/après
        
        Returns:
            Contexte extrait
        """
        if not match_text or not full_text:
            return ""
        
        pos = full_text.find(match_text)
        if pos == -1:
            return ""
        
        start = max(0, pos - window)
        end = min(len(full_text), pos + len(match_text) + window)
        
        return full_text[start:end]