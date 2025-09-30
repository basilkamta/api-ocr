from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from typing import List, Optional

from ....schemas.document import DocumentResponse, DocumentListResponse, DocumentUploadResponse
from ....dependencies import get_current_api_key

router = APIRouter()

@router.get("/", response_model=DocumentListResponse, tags=["Documents"])
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    api_key: str = Depends(get_current_api_key)
):
    """
    Liste tous les documents avec filtres et pagination
    
    - **skip**: Nombre de documents à sauter
    - **limit**: Nombre maximum de documents à retourner
    - **status**: Filtrer par statut (pending, processed, failed)
    - **date_from**: Date de début (YYYY-MM-DD)
    - **date_to**: Date de fin (YYYY-MM-DD)
    """
    # À implémenter avec DB
    return DocumentListResponse(
        documents=[],
        total=0,
        skip=skip,
        limit=limit
    )

@router.get("/{doc_id}", response_model=DocumentResponse, tags=["Documents"])
async def get_document(
    doc_id: str,
    api_key: str = Depends(get_current_api_key)
):
    """
    Détails d'un document spécifique
    """
    # À implémenter avec DB
    raise HTTPException(404, "Document non trouvé")

@router.post("/upload", response_model=DocumentUploadResponse, tags=["Documents"])
async def upload_document(
    file: UploadFile = File(...),
    description: Optional[str] = None,
    api_key: str = Depends(get_current_api_key)
):
    """
    Upload un document sans traitement immédiat
    """
    # À implémenter avec stockage
    return DocumentUploadResponse(
        doc_id="doc_123",
        filename=file.filename,
        message="Document uploadé avec succès"
    )

@router.delete("/{doc_id}", tags=["Documents"])
async def delete_document(
    doc_id: str,
    api_key: str = Depends(get_current_api_key)
):
    """
    Supprime un document
    """
    # À implémenter avec DB
    return {"message": "Document supprimé", "doc_id": doc_id}

@router.get("/{doc_id}/preview", tags=["Documents"])
async def preview_document(
    doc_id: str,
    page: int = Query(1, ge=1),
    api_key: str = Depends(get_current_api_key)
):
    """
    Génère un aperçu du document (image)
    """
    # À implémenter
    return {"message": "Preview generation - à implémenter"}

@router.get("/{doc_id}/download", tags=["Documents"])
async def download_document(
    doc_id: str,
    api_key: str = Depends(get_current_api_key)
):
    """
    Télécharge le document original
    """
    # À implémenter avec FileResponse
    raise HTTPException(404, "Document non trouvé")

@router.patch("/{doc_id}", tags=["Documents"])
async def update_document(
    doc_id: str,
    update_data: dict,
    api_key: str = Depends(get_current_api_key)
):
    """
    Met à jour les métadonnées d'un document
    """
    # À implémenter avec DB
    return {"message": "Document mis à jour", "doc_id": doc_id}

@router.get("/search", tags=["Documents"])
async def search_documents(
    q: str = Query(..., min_length=3),
    field: Optional[str] = None,
    api_key: str = Depends(get_current_api_key)
):
    """
    Recherche dans les documents
    
    - **q**: Terme de recherche
    - **field**: Champ spécifique (mandat, bordereau, etc.)
    """
    # À implémenter avec recherche full-text
    return {"results": [], "query": q}

@router.get("/stats", tags=["Documents"])
async def get_documents_stats(
    api_key: str = Depends(get_current_api_key)
):
    """
    Statistiques sur les documents
    """
    return {
        "total_documents": 0,
        "processed": 0,
        "pending": 0,
        "failed": 0,
        "by_engine": {}
    }
