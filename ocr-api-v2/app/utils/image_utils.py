import cv2
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class ImagePreprocessor:
    """Preprocessing d'images pour améliorer l'OCR"""
    
    @staticmethod
    def preprocess(image: np.ndarray, mode: str = "standard") -> np.ndarray:
        """
        Applique le preprocessing selon le mode
        
        Args:
            image: Image numpy array
            mode: "fast", "standard", ou "accurate"
        """
        if mode == "fast":
            return ImagePreprocessor._fast_preprocess(image)
        elif mode == "accurate":
            return ImagePreprocessor._accurate_preprocess(image)
        else:  # standard
            return ImagePreprocessor._standard_preprocess(image)
    
    @staticmethod
    def _fast_preprocess(image: np.ndarray) -> np.ndarray:
        """Preprocessing rapide"""
        # Juste conversion en RGB
        if len(image.shape) == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        return image
    
    @staticmethod
    def _standard_preprocess(image: np.ndarray) -> np.ndarray:
        """Preprocessing standard"""
        # Conversion RGB
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        
        # Amélioration du contraste
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)
        
        return enhanced
    
    @staticmethod
    def _accurate_preprocess(image: np.ndarray) -> np.ndarray:
        """Preprocessing complet pour haute précision"""
        # Conversion RGB
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        
        # Débruitage
        denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        
        # Amélioration contraste
        lab = cv2.cvtColor(denoised, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)
        
        # Correction gamma
        gamma = 1.2
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype("uint8")
        adjusted = cv2.LUT(enhanced, table)
        
        return adjusted
    
    @staticmethod
    def pdf_to_image(pdf_path: str, dpi: int = 300) -> np.ndarray:
        """Convertit un PDF en image"""
        import fitz
        
        doc = fitz.open(pdf_path)
        page = doc[0]
        
        matrix = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=matrix)
        
        # Conversion en numpy array
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        
        # Conversion RGB si nécessaire
        if pix.n == 4:  # RGBA
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
        
        doc.close()
        return img
