"""
Extracteur principal de métadonnées à partir du texte OCR
"""
from typing import Dict, List, Optional, Any
import logging

from ..utils.pattern_utils import PatternMatcher, normalize_amount, format_mandat_reference, format_bordereau_reference
from ..utils.text_utils import clean_ocr_artifacts, normalize_whitespace
from ..utils.date_utils import extract_dates_from_text, extract_emission_date
from ..schemas.ocr import DocumentInfo

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """
    Extracteur de métadonnées depuis le texte OCR
    
    Extrait:
    - Numéros de mandat
    - Numéros de bordereau
    - Exercice fiscal
    - Dates
    - Montants
    - Bénéficiaires
    """
    
    def __init__(self):
        self.pattern_matcher = PatternMatcher()
    
    def extract_all(
        self,
        text: str,
        coordinates: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Extrait toutes les métadonnées depuis le texte
        
        Args:
            text: Texte brut extrait par OCR
            coordinates: Optionnel, liste de {text, bbox, confidence} pour chaque élément
        
        Returns:
            Dictionnaire avec toutes les métadonnées extraites
        """
        if not text:
            logger.warning("Texte vide pour extraction")
            return self._empty_metadata()
        
        # Nettoyage du texte
        clean_text = self._clean_text(text)
        
        # Extraction des métadonnées
        metadata = {
            'mandat': self.extract_mandat(clean_text, coordinates),
            'bordereau': self.extract_bordereau(clean_text, coordinates),
            'exercice': self.extract_exercice(clean_text),
            'dates': self.extract_dates(clean_text),
            'amounts': self.extract_amounts(clean_text),
            'beneficiaire': self.extract_beneficiaire(clean_text),
        }
        
        logger.info(
            f"Extraction terminée: "
            f"mandat={'✓' if metadata['mandat'] else '✗'}, "
            f"bordereau={'✓' if metadata['bordereau'] else '✗'}, "
            f"exercice={'✓' if metadata['exercice'] else '✗'}"
        )
        
        return metadata
    
    def extract_mandat(
        self,
        text: str,
        coordinates: Optional[List[Dict]] = None
    ) -> Optional[DocumentInfo]:
        """
        Extrait le numéro de mandat
        
        Format: MD/XXXXXXX (ex: MD/2412034)
        """
        if not text:
            return None
        
        # Utiliser les patterns
        number = self.pattern_matcher.extract_mandat(text)
        
        if not number:
            return None
        
        # Validation du format
        if not self.pattern_matcher.validate_mandat_format(number):
            logger.warning(f"Format mandat invalide: {number}")
            return None
        
        # Recherche des coordonnées si disponibles
        bbox = self._find_coordinates(f"MD/{number}", coordinates) if coordinates else None
        confidence = bbox.get('confidence', 0.85) if bbox else 0.85
        
        return DocumentInfo(
            type="mandat",
            number=number,
            full_reference=format_mandat_reference(number),
            confidence=confidence,
            coordinates=bbox.get('bbox') if bbox else None
        )
    
    def extract_bordereau(
        self,
        text: str,
        coordinates: Optional[List[Dict]] = None
    ) -> Optional[DocumentInfo]:
        """
        Extrait le numéro de bordereau
        
        Format: BOR/XXXXXXX (ex: BOR/2402756)
        """
        if not text:
            return None
        
        number = self.pattern_matcher.extract_bordereau(text)
        
        if not number:
            return None
        
        if not self.pattern_matcher.validate_bordereau_format(number):
            logger.warning(f"Format bordereau invalide: {number}")
            return None
        
        bbox = self._find_coordinates(f"BOR/{number}", coordinates) if coordinates else None
        confidence = bbox.get('confidence', 0.85) if bbox else 0.85
        
        return DocumentInfo(
            type="bordereau",
            number=number,
            full_reference=format_bordereau_reference(number),
            confidence=confidence,
            coordinates=bbox.get('bbox') if bbox else None
        )
    
    def extract_exercice(self, text: str) -> Optional[str]:
        """
        Extrait l'exercice fiscal
        
        Format: AAAA (ex: 2024)
        """
        if not text:
            return None
        
        exercice = self.pattern_matcher.extract_exercice(text)
        
        if exercice:
            logger.debug(f"Exercice trouvé: {exercice}")
        
        return exercice
    
    def extract_dates(self, text: str) -> List[Dict]:
        """
        Extrait toutes les dates du document
        
        Returns:
            Liste de {value: str, formatted: str, type: str, confidence: float}
        """
        if not text:
            return []
        
        dates_found = extract_dates_from_text(text)
        
        result = []
        for date_info in dates_found:
            result.append({
                'value': date_info['date'].isoformat(),
                'formatted': date_info['raw'],
                'type': self._categorize_date(date_info['raw'], text),
                'confidence': 0.80
            })
        
        return result
    
    def extract_amounts(self, text: str) -> List[Dict]:
        """
        Extrait tous les montants du document
        
        Returns:
            Liste de {value: float, currency: str, formatted: str, confidence: float}
        """
        if not text:
            return []
        
        amounts_raw = self.pattern_matcher.extract_all_amounts(text)
        
        result = []
        for amount_str in amounts_raw:
            normalized = normalize_amount(amount_str)
            if normalized and normalized > 0:
                result.append({
                    'value': normalized,
                    'currency': 'XAF',  # Franc CFA
                    'formatted': f"{int(normalized):,} FCFA".replace(',', ' '),
                    'type': self._categorize_amount(amount_str, text),
                    'confidence': 0.85
                })
        
        return result
    
    def extract_beneficiaire(self, text: str) -> Optional[Dict]:
        """
        Extrait le bénéficiaire du document
        
        Returns:
            {name: str, confidence: float} ou None
        """
        if not text:
            return None
        
        matches = self.pattern_matcher.find_all_matches(
            text,
            self.pattern_matcher.BENEFICIAIRE_PATTERNS
        )
        
        if not matches:
            return None
        
        best_match = matches[0]
        beneficiaire_name = best_match['groups'][0] if best_match['groups'] else None
        
        if not beneficiaire_name:
            return None
        
        # Nettoyage du nom
        beneficiaire_name = beneficiaire_name.strip()
        
        return {
            'name': beneficiaire_name,
            'confidence': 0.75
        }
    
    # =================================================================
    # MÉTHODES PRIVÉES
    # =================================================================
    
    def _clean_text(self, text: str) -> str:
        """Nettoie le texte OCR avant extraction"""
        if not text:
            return ""
        
        # Supprimer artéfacts OCR
        text = clean_ocr_artifacts(text)
        
        # Normaliser espaces
        text = normalize_whitespace(text)
        
        return text
    
    def _find_coordinates(self, search_text: str, coordinates: List[Dict]) -> Optional[Dict]:
        """
        Trouve les coordonnées d'un texte dans la liste des résultats OCR
        
        Args:
            search_text: Texte à chercher
            coordinates: Liste de {text, bbox, confidence}
        
        Returns:
            Dictionnaire avec bbox et confidence, ou None
        """
        if not coordinates:
            return None
        
        for item in coordinates:
            if search_text.lower() in item.get('text', '').lower():
                return {
                    'bbox': item.get('bbox'),
                    'confidence': item.get('confidence', 0.85)
                }
        
        return None
    
    def _categorize_date(self, date_str: str, full_text: str) -> str:
        """
        Catégorise une date selon son contexte
        
        Returns: 'emission', 'paiement', 'signature', 'echeance', 'autre'
        """
        # Chercher le contexte autour de la date
        context_length = 50
        date_pos = full_text.lower().find(date_str.lower())
        
        if date_pos == -1:
            return 'autre'
        
        # Contexte avant la date
        start = max(0, date_pos - context_length)
        context_before = full_text[start:date_pos].lower()
        
        # Mots-clés pour chaque type
        if any(word in context_before for word in ['émission', 'emission', 'émis', 'emis', 'fait']):
            return 'emission'
        elif any(word in context_before for word in ['paiement', 'payé', 'paye', 'règlement', 'reglement']):
            return 'paiement'
        elif any(word in context_before for word in ['signé', 'signe', 'signature']):
            return 'signature'
        elif any(word in context_before for word in ['échéance', 'echeance', 'limite']):
            return 'echeance'
        
        return 'autre'
    
    def _categorize_amount(self, amount_str: str, full_text: str) -> str:
        """
        Catégorise un montant selon son contexte
        
        Returns: 'total', 'net', 'brut', 'taxe', 'autre'
        """
        # Chercher le contexte
        amount_pos = full_text.lower().find(amount_str.lower())
        
        if amount_pos == -1:
            return 'autre'
        
        context_length = 30
        start = max(0, amount_pos - context_length)
        context_before = full_text[start:amount_pos].lower()
        
        if any(word in context_before for word in ['total', 'somme']):
            return 'total'
        elif 'net' in context_before:
            return 'net'
        elif 'brut' in context_before:
            return 'brut'
        elif any(word in context_before for word in ['taxe', 'tva', 'impot', 'impôt']):
            return 'taxe'
        
        return 'autre'
    
    def _empty_metadata(self) -> Dict[str, Any]:
        """Retourne une structure vide de métadonnées"""
        return {
            'mandat': None,
            'bordereau': None,
            'exercice': None,
            'dates': [],
            'amounts': [],
            'beneficiaire': None,
        }
    
    # =================================================================
    # MÉTHODES DE VALIDATION
    # =================================================================
    
    def validate_extraction(self, metadata: Dict) -> Dict[str, Any]:
        """
        Valide les métadonnées extraites
        
        Returns:
            {is_valid: bool, errors: List[str], warnings: List[str]}
        """
        errors = []
        warnings = []
        
        # Validation mandat
        if metadata.get('mandat'):
            mandat_num = metadata['mandat'].number
            if not self.pattern_matcher.validate_mandat_format(mandat_num):
                errors.append(f"Format mandat invalide: {mandat_num}")
        else:
            warnings.append("Aucun mandat trouvé")
        
        # Validation bordereau
        if metadata.get('bordereau'):
            bordereau_num = metadata['bordereau'].number
            if not self.pattern_matcher.validate_bordereau_format(bordereau_num):
                errors.append(f"Format bordereau invalide: {bordereau_num}")
        else:
            warnings.append("Aucun bordereau trouvé")
        
        # Validation exercice
        if metadata.get('exercice'):
            exercice = metadata['exercice']
            try:
                year = int(exercice)
                if not (2015 <= year <= 2030):
                    warnings.append(f"Exercice hors plage valide: {exercice}")
            except ValueError:
                errors.append(f"Exercice invalide: {exercice}")
        else:
            warnings.append("Aucun exercice trouvé")
        
        # Validation cohérence mandat-exercice
        if metadata.get('mandat') and metadata.get('exercice'):
            mandat_year_prefix = metadata['mandat'].number[:2]
            exercice_suffix = metadata['exercice'][-2:]
            
            if mandat_year_prefix != exercice_suffix:
                warnings.append(
                    f"Incohérence année mandat ({mandat_year_prefix}) et exercice ({exercice_suffix})"
                )
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'confidence': self._calculate_overall_confidence(metadata)
        }
    
    def _calculate_overall_confidence(self, metadata: Dict) -> float:
        """
        Calcule un score de confiance global
        
        Pondération:
        - Mandat: 40%
        - Bordereau: 30%
        - Exercice: 20%
        - Dates/Montants: 10%
        """
        total_weight = 0.0
        weighted_sum = 0.0
        
        # Mandat
        if metadata.get('mandat'):
            weighted_sum += metadata['mandat'].confidence * 0.4
            total_weight += 0.4
        
        # Bordereau
        if metadata.get('bordereau'):
            weighted_sum += metadata['bordereau'].confidence * 0.3
            total_weight += 0.3
        
        # Exercice
        if metadata.get('exercice'):
            weighted_sum += 0.9 * 0.2  # Confiance fixe pour exercice
            total_weight += 0.2
        
        # Dates et montants
        if metadata.get('dates') or metadata.get('amounts'):
            weighted_sum += 0.8 * 0.1
            total_weight += 0.1
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
    
    # =================================================================
    # MÉTHODES UTILITAIRES
    # =================================================================
    
    def get_extraction_summary(self, metadata: Dict) -> Dict[str, Any]:
        """
        Génère un résumé de l'extraction
        
        Utile pour le logging et le debugging
        """
        return {
            'has_mandat': metadata.get('mandat') is not None,
            'has_bordereau': metadata.get('bordereau') is not None,
            'has_exercice': metadata.get('exercice') is not None,
            'dates_count': len(metadata.get('dates', [])),
            'amounts_count': len(metadata.get('amounts', [])),
            'has_beneficiaire': metadata.get('beneficiaire') is not None,
            'mandat_ref': metadata['mandat'].full_reference if metadata.get('mandat') else None,
            'bordereau_ref': metadata['bordereau'].full_reference if metadata.get('bordereau') else None,
            'exercice': metadata.get('exercice'),
        }
