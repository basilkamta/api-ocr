from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

class StandardResponse(BaseModel):
    """Réponse standard"""
    success: bool
    message: str
    data: Optional[Any] = None

class HealthResponse(BaseModel):
    """Réponse santé basique"""
    status: str = Field(..., description="Statut de l'API")
    version: str = Field(..., description="Version de l'API")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DetailedHealthResponse(BaseModel):
    """Réponse santé détaillée"""
    status: str
    version: str
    timestamp: datetime
    engines: List[Dict]
    system: Dict[str, Any]
    config: Dict[str, Any]