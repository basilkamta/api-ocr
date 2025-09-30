"""
Extracteur spécialisé pour les dates
"""
from typing import List, Dict, Optional
from datetime import datetime
import logging

from ..utils.date_utils import (
    extract_dates_from_text,
    extract_emission_date,
    extract_payment_date,
    extract_signature_date,
    format_date_french
)
from .base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class DateExtractor(BaseExtractor):
    """
    Extracteur spécialisé pour les dates
    
    Extrait et catégorise:
    - Date d'émission
    - Date de paiement
    - Date de signature
    - Autres dates du document
    """
    
    def extract(self, text: str, **kwargs) -> List[Dict]:
        """
        Extrait toutes les dates du texte
        
        Returns:
            Liste de {
                date: datetime,
                formatted: str,
                type: str,
                confidence: float
            }
        """
        if not text:
            return []
        
        # Extraction de toutes les dates
        dates_found = extract_dates_from_text(text)
        
        # Catégorisation spécifique
        emission_date = extract_emission_date(text)
        payment_date = extract_payment_date(text)
        signature_date = extract_signature_date(text)
        
        results = []
        processed_dates = set()
        
        # Ajouter les dates spécifiques d'abord
        if emission_date:
            results.append({
                'date': emission_date,
                'formatted': format_date_french(emission_date),
                'type': 'emission',
                'confidence': 0.90
            })
            processed_dates.add(emission_date.date())
        
        if payment_date and payment_date.date() not in processed_dates:
            results.append({
                'date': payment_date,
                'formatted': format_date_french(payment_date),
                'type': 'paiement',
                'confidence': 0.85
            })
            processed_dates.add(payment_date.date())
        
        if signature_date and signature_date.date() not in processed_dates:
            results.append({
                'date': signature_date,
                'formatted': format_date_french(signature_date),
                'type': 'signature',
                'confidence': 0.85
            })
            processed_dates.add(signature_date.date())
        
        # Ajouter les autres dates
        for date_info in dates_found:
            date_obj = date_info['date']
            if date_obj.date() not in processed_dates:
                results.append({
                    'date': date_obj,
                    'formatted': date_info['raw'],
                    'type': 'autre',
                    'confidence': 0.75
                })
                processed_dates.add(date_obj.date())
        
        logger.info(f"{len(results)} date(s) extraite(s)")
        return results
    
    def validate(self, data: List[Dict]) -> bool:
        """Valide les dates extraites"""
        if not data:
            return False
        
        # Vérifier que toutes les dates sont valides
        for date_info in data:
            if 'date' not in date_info or not isinstance(date_info['date'], datetime):
                return False
        
        return True
    
    def extract_emission_date_only(self, text: str) -> Optional[Dict]:
        """Extrait uniquement la date d'émission"""
        emission_date = extract_emission_date(text)
        
        if not emission_date:
            return None
        
        return {
            'date': emission_date,
            'formatted': format_date_french(emission_date),
            'type': 'emission',
            'confidence': 0.90
        }
    
    def extract_by_type(self, text: str, date_type: str) -> Optional[Dict]:
        """
        Extrait une date par type spécifique
        
        Args:
            text: Texte à analyser
            date_type: 'emission', 'paiement', 'signature'
        
        Returns:
            Dictionnaire avec la date ou None
        """
        extractors = {
            'emission': extract_emission_date,
            'paiement': extract_payment_date,
            'signature': extract_signature_date,
        }
        
        extractor = extractors.get(date_type)
        if not extractor:
            return None
        
        date_obj = extractor(text)
        if not date_obj:
            return None
        
        return {
            'date': date_obj,
            'formatted': format_date_french(date_obj),
            'type': date_type,
            'confidence': 0.85
        }
    
    def get_most_recent_date(self, dates: List[Dict]) -> Optional[Dict]:
        """Retourne la date la plus récente"""
        if not dates:
            return None
        
        return max(dates, key=lambda x: x['date'])
    
    def get_oldest_date(self, dates: List[Dict]) -> Optional[Dict]:
        """Retourne la date la plus ancienne"""
        if not dates:
            return None
        
        return min(dates, key=lambda x: x['date'])
    
    def filter_by_year(self, dates: List[Dict], year: int) -> List[Dict]:
        """Filtre les dates par année"""
        return [d for d in dates if d['date'].year == year]
    
    def filter_by_type(self, dates: List[Dict], date_type: str) -> List[Dict]:
        """Filtre les dates par type"""
        return [d for d in dates if d.get('type') == date_type]