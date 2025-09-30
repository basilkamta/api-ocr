"""
Extracteur spécialisé pour l'exercice fiscal
"""
from typing import Optional
import logging

from ..utils.pattern_utils import PatternMatcher

logger = logging.getLogger(__name__)


class ExerciceExtractor:
    """
    Extracteur spécialisé pour l'exercice fiscal
    
    Formats supportés:
    - Exercice: 2024
    - Gestion budgétaire: 2024
    - GB/2024
    - Année isolée dans contexte administratif
    """
    
    def __init__(self):
        self.pattern_matcher = PatternMatcher()
    
    def extract(self, text: str) -> Optional[str]:
        """
        Extrait l'exercice fiscal du texte
        
        Returns:
            Année au format AAAA (ex: "2024") ou None
        """
        if not text:
            return None
        
        exercice = self.pattern_matcher.extract_exercice(text)
        
        if exercice:
            logger.info(f"Exercice fiscal extrait: {exercice}")
        else:
            logger.debug("Aucun exercice fiscal trouvé")
        
        return exercice
    
    def validate(self, exercice: str) -> bool:
        """
        Valide un exercice fiscal
        
        Règles:
        - 4 chiffres
        - Entre 2015 et 2030
        """
        if not exercice or not isinstance(exercice, str):
            return False
        
        if not exercice.isdigit() or len(exercice) != 4:
            return False
        
        try:
            year = int(exercice)
            return 2015 <= year <= 2030
        except ValueError:
            return False
    
    def extract_from_date(self, date_str: str) -> Optional[str]:
        """
        Extrait l'exercice depuis une date
        
        Ex: "15/12/2024" -> "2024"
        """
        import re
        
        # Format JJ/MM/AAAA
        match = re.search(r'\d{2}/\d{2}/(\d{4})', date_str)
        if match:
            year = match.group(1)
            if self.validate(year):
                return year
        
        # Format AAAA-MM-JJ
        match = re.search(r'(\d{4})-\d{2}-\d{2}', date_str)
        if match:
            year = match.group(1)
            if self.validate(year):
                return year
        
        return None