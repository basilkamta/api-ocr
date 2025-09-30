from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
import time
import uuid

from .logging import get_logger
from .metrics import REQUEST_COUNT, REQUEST_DURATION

logger = get_logger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Ajoute un ID unique à chaque requête"""
    
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    """Log toutes les requêtes"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log de la requête
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            request_id=getattr(request.state, "request_id", None)
        )
        
        response = await call_next(request)
        
        # Log de la réponse
        duration = time.time() - start_time
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=duration,
            request_id=getattr(request.state, "request_id", None)
        )
        
        return response

class TimingMiddleware(BaseHTTPMiddleware):
    """Ajoute le temps de traitement dans les headers"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        response.headers["X-Process-Time"] = str(process_time)
        
        return response