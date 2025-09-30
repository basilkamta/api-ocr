
from .session import engine
from ..models.base import Base
from ..models.ocr import OCRResult
from ..models.document import Document
from ..models.batch import Batch
from ..models.user import User, APIKey

def create_tables():
    """Crée toutes les tables"""
    Base.metadata.create_all(bind=engine)