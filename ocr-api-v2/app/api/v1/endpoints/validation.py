from fastapi import APIRouter, Depends, Body

from ....schemas.validation import ValidationRequest, ValidationResponse, HierarchyValidationRequest
from ....dependencies import get_current_api_key

router = APIRouter()

@router.post("/validate", response_model=ValidationResponse, tags=["Validation"])
async def validate_metadata(
    request: ValidationRequest = Body(...),
    api_key: str = Depends(get_current_api_key)
):
    """
    Valide des métadonnées extraites
    
    Vérifie:
    - Format des numéros
    - Cohérence des données
    - Règles métier
    """
    # À implémenter avec validators
    return ValidationResponse(
        is_valid=True,
        errors=[],
        warnings=[]
    )

@router.post("/mandat", tags=["Validation"])
async def validate_mandat(
    mandat_number: str = Body(...),
    api_key: str = Depends(get_current_api_key)
):
    """
    Valide un numéro de mandat
    """
    # À implémenter
    return {"valid": True, "mandat": mandat_number}

@router.post("/bordereau", tags=["Validation"])
async def validate_bordereau(
    bordereau_number: str = Body(...),
    api_key: str = Depends(get_current_api_key)
):
    """
    Valide un numéro de bordereau
    """
    # À implémenter
    return {"valid": True, "bordereau": bordereau_number}

@router.post("/hierarchy", tags=["Validation"])
async def validate_hierarchy(
    request: HierarchyValidationRequest = Body(...),
    api_key: str = Depends(get_current_api_key)
):
    """
    Valide la hiérarchie mandat-bordereau
    
    Vérifie que le mandat appartient bien au bordereau
    """
    # À implémenter avec logique ERP
    return {
        "valid": True,
        "mandat": request.mandat,
        "bordereau": request.bordereau,
        "message": "Hiérarchie valide"
    }

@router.get("/rules", tags=["Validation"])
async def list_validation_rules(
    api_key: str = Depends(get_current_api_key)
):
    """
    Liste toutes les règles de validation
    """
    return {
        "rules": [
            {
                "id": "format_mandat",
                "description": "Format MD/XXXXXXX",
                "type": "format"
            },
            {
                "id": "format_bordereau",
                "description": "Format BOR/XXXXXXX",
                "type": "format"
            }
        ]
    }

@router.post("/custom-rule", tags=["Validation"])
async def add_custom_rule(
    rule: dict = Body(...),
    api_key: str = Depends(get_current_api_key)
):
    """
    Ajoute une règle de validation personnalisée
    """
    # À implémenter
    return {"message": "Règle ajoutée", "rule_id": "custom_001"}
