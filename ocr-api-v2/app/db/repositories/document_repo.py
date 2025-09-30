from sqlalchemy.orm import Session
from typing import List, Optional

from ...models.document import Document
from ...schemas.document import DocumentStatus

class DocumentRepository:
    """Repository pour les documents"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, **kwargs) -> Document:
        """Crée un document"""
        document = Document(**kwargs)
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document
    
    def get_by_id(self, doc_id: str) -> Optional[Document]:
        """Récupère par ID"""
        return self.db.query(Document).filter(Document.id == doc_id).first()
    
    def list_documents(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[DocumentStatus] = None
    ) -> List[Document]:
        """Liste les documents"""
        query = self.db.query(Document)
        
        if status:
            query = query.filter(Document.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    def update_status(self, doc_id: str, status: DocumentStatus) -> Optional[Document]:
        """Met à jour le statut"""
        document = self.get_by_id(doc_id)
        if document:
            document.status = status
            self.db.commit()
            self.db.refresh(document)
        return document
    
    def delete(self, doc_id: str) -> bool:
        """Supprime un document"""
        document = self.get_by_id(doc_id)
        if document:
            self.db.delete(document)
            self.db.commit()
            return True
        return False
    
    def search(self, query: str, field: Optional[str] = None) -> List[Document]:
        """Recherche dans les documents"""
        # Implémentation de recherche simple
        # Pour une vraie recherche full-text, utiliser PostgreSQL FTS
        search_query = self.db.query(Document)
        search_query = search_query.filter(Document.filename.ilike(f"%{query}%"))
        return search_query.all()