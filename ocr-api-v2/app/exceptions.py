from fastapi import HTTPException, status

class OCRException(Exception):
    """Exception de base pour l'OCR"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class EngineNotAvailableException(OCRException):
    """Moteur OCR non disponible"""
    def __init__(self, engine: str):
        super().__init__(
            f"Le moteur OCR '{engine}' n'est pas disponible",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

class ExtractionFailedException(OCRException):
    """Échec de l'extraction OCR"""
    def __init__(self, reason: str):
        super().__init__(
            f"Échec de l'extraction: {reason}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

class InvalidFileException(OCRException):
    """Fichier invalide"""
    def __init__(self, reason: str):
        super().__init__(
            f"Fichier invalide: {reason}",
            status_code=status.HTTP_400_BAD_REQUEST
        )

class ValidationException(OCRException):
    """Erreur de validation"""
    def __init__(self, errors: list):
        super().__init__(
            f"Erreurs de validation: {errors}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
