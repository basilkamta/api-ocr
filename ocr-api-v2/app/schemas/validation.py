from pydantic import BaseModel
from typing import List, Optional

class ValidationError(BaseModel):
    """Erreur de validation"""
    field: str
    message: str
    code: str

class ValidationWarning(BaseModel):
    """Avertissement de validation"""
    field: str
    message: str

class ValidationRequest(BaseModel):
    """Requête de validation"""
    mandat: Optional[str] = None
    bordereau: Optional[str] = None
    exercice: Optional[str] = None
    strict_mode: bool = False

class ValidationResponse(BaseModel):
    """Réponse de validation"""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationWarning]
    confidence: float = 1.0

class HierarchyValidationRequest(BaseModel):
    """Requête de validation hiérarchique"""
    mandat: str
    bordereau: str
    check_erp: bool = False