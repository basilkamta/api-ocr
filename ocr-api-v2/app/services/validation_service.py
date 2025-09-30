"""
Service de validation centralisé
"""
import logging
from typing import Dict, List, Optional, Any

from ..validators.format_validator import FormatValidator
from ..validators.mandat_validator import MandatValidator
from ..validators.bordereau_validator import BordereauValidator
from ..validators.business_validator import BusinessValidator
from ..validators.base_validator import ValidationResult

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Service centralisé de validation
    
    Coordonne tous les validators et fournit une API unifiée
    """
    
    def __init__(self):
        self.format_validator = FormatValidator()
        self.mandat_validator = MandatValidator()
        self.bordereau_validator = BordereauValidator()
        self.business_validator = BusinessValidator()
        
        logger.info("ValidationService initialisé")
    
    async def validate_extraction(self, metadata: Dict) -> Dict[str, Any]:
        """
        Valide une extraction OCR complète
        
        Args:
            metadata: Métadonnées extraites (mandat, bordereau, exercice, etc.)
        
        Returns:
            Dict avec résultats de validation
        """
        all_errors = []
        all_warnings = []
        validations = {}
        
        # 1. Validation de format
        logger.debug("Validation des formats...")
        format_data = {}
        
        if metadata.get('mandat'):
            format_data['mandat'] = metadata['mandat'].number if hasattr(metadata['mandat'], 'number') else metadata['mandat']
        
        if metadata.get('bordereau'):
            format_data['bordereau'] = metadata['bordereau'].number if hasattr(metadata['bordereau'], 'number') else metadata['bordereau']
        
        if metadata.get('exercice'):
            format_data['exercice'] = metadata['exercice']
        
        format_result = self.format_validator.validate(format_data)
        validations['format'] = format_result.to_dict()
        
        all_errors.extend(format_result.errors)
        all_warnings.extend(format_result.warnings)
        
        # 2. Validation spécifique mandat
        if metadata.get('mandat'):
            logger.debug("Validation mandat...")
            mandat_data = {
                'number': metadata['mandat'].number if hasattr(metadata['mandat'], 'number') else metadata['mandat'],
                'exercice': metadata.get('exercice')
            }
            mandat_result = self.mandat_validator.validate(mandat_data)
            validations['mandat'] = mandat_result.to_dict()
            
            all_errors.extend(mandat_result.errors)
            all_warnings.extend(mandat_result.warnings)
        
        # 3. Validation spécifique bordereau
        if metadata.get('bordereau'):
            logger.debug("Validation bordereau...")
            bordereau_data = {
                'number': metadata['bordereau'].number if hasattr(metadata['bordereau'], 'number') else metadata['bordereau']
            }
            bordereau_result = self.bordereau_validator.validate(bordereau_data)
            validations['bordereau'] = bordereau_result.to_dict()
            
            all_errors.extend(bordereau_result.errors)
            all_warnings.extend(bordereau_result.warnings)
        
        # 4. Validation des règles métier
        logger.debug("Validation règles métier...")
        business_result = self.business_validator.validate(metadata)
        validations['business'] = business_result.to_dict()
        
        all_errors.extend(business_result.errors)
        all_warnings.extend(business_result.warnings)
        
        # 5. Validation hiérarchie si applicable
        if metadata.get('mandat') and metadata.get('bordereau'):
            logger.debug("Validation hiérarchie...")
            mandat_num = metadata['mandat'].number if hasattr(metadata['mandat'], 'number') else metadata['mandat']
            bordereau_num = metadata['bordereau'].number if hasattr(metadata['bordereau'], 'number') else metadata['bordereau']
            
            hierarchy_result = self.business_validator.validate_hierarchy(mandat_num, bordereau_num)
            validations['hierarchy'] = hierarchy_result.to_dict()
            
            all_errors.extend(hierarchy_result.errors)
            all_warnings.extend(hierarchy_result.warnings)
        
        # Résumé global
        is_valid = len(all_errors) == 0
        
        return {
            'is_valid': is_valid,
            'errors': [e.to_dict() for e in all_errors],
            'warnings': [w.to_dict() for w in all_warnings],
            'validations': validations,
            'summary': {
                'total_errors': len(all_errors),
                'total_warnings': len(all_warnings),
                'validators_run': len(validations)
            }
        }
    
    async def validate_mandat_only(self, mandat_number: str, exercice: Optional[str] = None) -> Dict:
        """
        Valide uniquement un mandat
        
        Args:
            mandat_number: Numéro de mandat
            exercice: Exercice fiscal (optionnel)
        
        Returns:
            Résultat de validation
        """
        result = self.mandat_validator.validate({
            'number': mandat_number,
            'exercice': exercice
        })
        
        return result.to_dict()
    
    async def validate_bordereau_only(self, bordereau_number: str) -> Dict:
        """
        Valide uniquement un bordereau
        
        Args:
            bordereau_number: Numéro de bordereau
        
        Returns:
            Résultat de validation
        """
        result = self.bordereau_validator.validate({
            'number': bordereau_number
        })
        
        return result.to_dict()
    
    async def validate_hierarchy(self, mandat_number: str, bordereau_number: str) -> Dict:
        """
        Valide la hiérarchie mandat-bordereau
        
        Args:
            mandat_number: Numéro de mandat
            bordereau_number: Numéro de bordereau
        
        Returns:
            Résultat de validation
        """
        result = self.business_validator.validate_hierarchy(mandat_number, bordereau_number)
        
        return result.to_dict()
    
    def get_validation_rules(self) -> List[Dict]:
        """
        Retourne la liste de toutes les règles de validation
        
        Returns:
            Liste de règles
        """
        return [
            {
                'id': 'format_mandat',
                'type': 'format',
                'description': 'Format BOR/XXXXXXX avec 7 chiffres',
                'validator': 'FormatValidator'
            },
            {
                'id': 'format_exercice',
                'type': 'format',
                'description': 'Année fiscale entre 2015 et 2030',
                'validator': 'FormatValidator'
            },
            {
                'id': 'mandat_year_consistency',
                'type': 'business',
                'description': 'Cohérence entre année du mandat et exercice fiscal',
                'validator': 'MandatValidator'
            },
            {
                'id': 'hierarchy_mandat_bordereau',
                'type': 'business',
                'description': 'Le mandat doit appartenir au bordereau',
                'validator': 'BusinessValidator'
            },
            {
                'id': 'amounts_consistency',
                'type': 'business',
                'description': 'Cohérence entre montants (total >= sous-totaux)',
                'validator': 'BusinessValidator'
            },
            {
                'id': 'dates_in_fiscal_year',
                'type': 'business',
                'description': 'Les dates doivent correspondre à l\'exercice fiscal',
                'validator': 'BusinessValidator'
            }
        ]
    
    async def add_custom_rule(self, rule: Dict) -> bool:
        """
        Ajoute une règle de validation personnalisée
        
        Args:
            rule: Définition de la règle
        
        Returns:
            True si ajoutée avec succès
        """
        # TODO: Implémenter le système de règles personnalisées
        logger.warning("add_custom_rule pas encore implémenté")
        return False
    
    async def validate_with_erp(self, mandat: str, bordereau: str) -> Dict:
        """
        Valide avec un système ERP externe
        
        Args:
            mandat: Numéro de mandat
            bordereau: Numéro de bordereau
        
        Returns:
            Résultat de validation ERP
        """
        # TODO: Intégration avec l'ERP client
        logger.warning("Validation ERP pas encore implémentée")
        
        return {
            'is_valid': None,
            'checked': False,
            'message': 'Validation ERP non configurée',
            'mandat': mandat,
            'bordereau': bordereau
        }


# =================================================================
# Instance globale (Singleton)
# =================================================================

_validation_service_instance: Optional[ValidationService] = None


def get_validation_service() -> ValidationService:
    """Récupère l'instance du service de validation (Singleton)"""
    global _validation_service_instance
    
    if _validation_service_instance is None:
        _validation_service_instance = ValidationService()
    
    return _validation_service_instance
