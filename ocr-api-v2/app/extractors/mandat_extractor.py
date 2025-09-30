"""
Extracteur spécialisé pour les mandats de paiement
"""
from typing import Optional, List, Dict
import re
import logging

from ..utils.pattern_utils import PatternMatcher, format_mandat_reference
from ..schemas.ocr import DocumentInfo

logger = logging.getLogger(__name__)


class MandatExtractor:
    """
    Extracteur spécialisé pour les numéros de mandat
    
    Formats supportés:
    - MD/2412034 (standard)
    - MD-2412034
    - MD 2412034
    - N° Mandat: MD/2412034
    - Mandat de Paiement N° MD/2412034
    """
    
    def __init__(self):
        self.pattern_matcher = PatternMatcher()
    
    def extract(self, text: str, coordinates: Optional[List[Dict]] = None) -> Optional[DocumentInfo]:
        """
        Extrait le numéro de mandat du texte
        
        Args:
            text: Texte OCR
            coordinates: Coordonnées des éléments détectés
        
        Returns:
            DocumentInfo avec les infos du mandat ou None
        """
        if not text:
            return None
        
        # Utiliser les patterns prédéfinis
        matches = self.pattern_matcher.find_all_matches(
            text,
            self.pattern_matcher.MANDAT_PATTERNS
        )
        
        if not matches:
            logger.debug("Aucun mandat trouvé dans le texte")
            return None
        
        # Prendre la meilleure correspondance (plus haute priorité)
        best_match = matches[0]
        number = best_match['groups'][0] if best_match['groups'] else None
        
        if not number:
            return None
        
        # Validation du format
        if not self.validate_format(number):
            logger.warning(f"Format mandat invalide: {number}")
            return None
        
        # Recherche des coordonnées
        bbox, confidence = self._find_bbox(number, text, coordinates)
        
        # Extraction du contexte
        context = self._extract_context(number, text)
        
        logger.info(f"Mandat extrait: MD/{number} (confiance: {confidence:.2f})")
        
        return DocumentInfo(
            type="mandat",
            number=number,
            full_reference=format_mandat_reference(number),
            confidence=confidence,
            coordinates=bbox
        )
    
    def extract_multiple(self, text: str) -> List[DocumentInfo]:
        """
        Extrait tous les mandats trouvés dans le texte
        
        Utile si le document contient plusieurs mandats
        """
        if not text:
            return []
        
        matches = self.pattern_matcher.find_all_matches(
            text,
            self.pattern_matcher.MANDAT_PATTERNS
        )
        
        mandats = []
        seen_numbers = set()
        
        for match in matches:
            number = match['groups'][0] if match['groups'] else None
            
            if not number or number in seen_numbers:
                continue
            
            if self.validate_format(number):
                mandats.append(DocumentInfo(
                    type="mandat",
                    number=number,
                    full_reference=format_mandat_reference(number),
                    confidence=0.85
                ))
                seen_numbers.add(number)
        
        return mandats
    
    def validate_format(self, number: str) -> bool:
        """
        Valide le format d'un numéro de mandat
        
        Règles:
        - 7 chiffres
        - Préfixe année valide (20-26 pour 2020-2026)
        """
        if not number or not isinstance(number, str):
            return False
        
        # Doit être uniquement des chiffres
        if not number.isdigit():
            return False
        
        # Longueur exacte: 7 chiffres
        if len(number) != 7:
            return False
        
        # Vérifier le préfixe année (2 premiers chiffres)
        year_prefix = number[:2]
        valid_prefixes = ['19', '20', '21', '22', '23', '24', '25', '26']
        
        if year_prefix not in valid_prefixes:
            logger.debug(f"Préfixe année invalide: {year_prefix}")
            return False
        
        return True
    
    def _find_bbox(
        self,
        number: str,
        text: str,
        coordinates: Optional[List[Dict]]
    ) -> tuple[Optional[Dict], float]:
        """
        Trouve les coordonnées du mandat dans le document
        
        Returns:
            (bbox_dict, confidence)
        """
        if not coordinates:
            return None, 0.85
        
        # Chercher MD/XXXXXXX dans les coordonnées
        search_patterns = [
            f"MD/{number}",
            f"MD-{number}",
            f"MD {number}",
            number
        ]
        
        for item in coordinates:
            item_text = item.get('text', '')
            
            for pattern in search_patterns:
                if pattern in item_text:
                    return item.get('bbox'), item.get('confidence', 0.85)
        
        return None, 0.85
    
    def _extract_context(self, number: str, text: str, context_length: int = 100) -> str:
        """
        Extrait le contexte autour du mandat
        
        Utile pour comprendre le type de mandat
        """
        # Chercher la position du numéro
        patterns = [f"MD/{number}", f"MD-{number}", f"MD {number}"]
        
        for pattern in patterns:
            pos = text.find(pattern)
            if pos != -1:
                start = max(0, pos - context_length)
                end = min(len(text), pos + len(pattern) + context_length)
                return text[start:end]
        
        return ""
    
    def extract_year(self, number: str) -> Optional[int]:
        """
        Extrait l'année depuis le numéro de mandat
        
        Ex: 2412034 -> 2024
        """
        if not self.validate_format(number):
            return None
        
        year_prefix = number[:2]
        return 2000 + int(year_prefix)
    
    def extract_serial(self, number: str) -> Optional[int]:
        """
        Extrait le numéro séquentiel du mandat
        
        Ex: 2412034 -> 12034
        """
        if not self.validate_format(number):
            return None
        
        return int(number[2:])
