from prometheus_client import Counter, Histogram, Gauge, generate_latest
from typing import Callable
import time

# Métriques globales
REQUEST_COUNT = Counter(
    'ocr_requests_total',
    'Total de requêtes OCR',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'ocr_request_duration_seconds',
    'Durée des requêtes OCR',
    ['method', 'endpoint']
)

EXTRACTION_COUNT = Counter(
    'ocr_extractions_total',
    'Total d\'extractions OCR',
    ['engine', 'status']
)

EXTRACTION_DURATION = Histogram(
    'ocr_extraction_duration_seconds',
    'Durée des extractions OCR',
    ['engine']
)

ACTIVE_REQUESTS = Gauge(
    'ocr_active_requests',
    'Requêtes OCR actives'
)

ENGINE_AVAILABILITY = Gauge(
    'ocr_engine_available',
    'Disponibilité des moteurs OCR',
    ['engine']
)

def track_request(endpoint: str, method: str = "POST"):
    """Décorateur pour tracker les requêtes"""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            ACTIVE_REQUESTS.inc()
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                status = "success"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
                REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
                ACTIVE_REQUESTS.dec()
        
        return wrapper
    return decorator
