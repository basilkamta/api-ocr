from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from ...models.ocr import OCRResult

class OCRResultRepository:
    """Repository pour les résultats OCR"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, **kwargs) -> OCRResult:
        """Crée un résultat OCR"""
        result = OCRResult(**kwargs)
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result
    
    def get_by_id(self, result_id: str) -> Optional[OCRResult]:
        """Récupère par ID"""
        return self.db.query(OCRResult).filter(OCRResult.id == result_id).first()
    
    def get_by_file_hash(self, file_hash: str) -> Optional[OCRResult]:
        """Récupère par hash de fichier (cache)"""
        return self.db.query(OCRResult).filter(OCRResult.file_hash == file_hash).first()
    
    def list_results(self, skip: int = 0, limit: int = 100, **filters) -> List[OCRResult]:
        """Liste les résultats avec pagination"""
        query = self.db.query(OCRResult)
        
        # Appliquer les filtres
        if filters.get('success') is not None:
            query = query.filter(OCRResult.success == filters['success'])
        
        if filters.get('engine'):
            query = query.filter(OCRResult.primary_engine == filters['engine'])
        
        return query.offset(skip).limit(limit).all()
    
    def delete(self, result_id: str) -> bool:
        """Supprime un résultat"""
        result = self.get_by_id(result_id)
        if result:
            self.db.delete(result)
            self.db.commit()
            return True
        return False
    
    def cleanup_old_results(self, days: int = 30) -> int:
        """Nettoie les résultats anciens"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = self.db.query(OCRResult).filter(
            OCRResult.created_at < cutoff_date
        ).delete()
        self.db.commit()
        return deleted