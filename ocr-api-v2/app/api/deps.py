
from fastapi import Depends, HTTPException, status
from typing import Optional

from ..dependencies import get_current_api_key
from ..config import get_settings

settings = get_settings()

async def verify_api_access(
    api_key: str = Depends(get_current_api_key)
) -> str:
    """Vérifie l'accès à l'API"""
    # Ici vous pouvez ajouter une logique de vérification plus complexe
    # (quotas, permissions, etc.)
    return api_key