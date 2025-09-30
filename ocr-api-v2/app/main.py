from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .core.logging import setup_logging, get_logger
from .core.middleware import RequestIDMiddleware, LoggingMiddleware, TimingMiddleware
from .core.metrics import generate_latest
from .exceptions import OCRException
from .api.v1.api import api_router

# Configuration
settings = get_settings()
setup_logging()
logger = get_logger(__name__)

# Création de l'application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API OCR Multi-Moteurs avec PaddleOCR, EasyOCR et Kraken",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middlewares personnalisés
app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(TimingMiddleware)

# Gestionnaire d'exceptions global
@app.exception_handler(OCRException)
async def ocr_exception_handler(request: Request, exc: OCRException):
    logger.error(
        "ocr_error",
        message=exc.message,
        status_code=exc.status_code,
        path=request.url.path
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "type": exc.__class__.__name__}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "unhandled_error",
        error=str(exc),
        path=request.url.path
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Erreur interne du serveur"}
    )

# Routes principales
@app.get("/", tags=["Root"])
async def root():
    """Page d'accueil de l'API"""
    return {
        "message": f"Bienvenue sur {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health"
    }

@app.get("/version", tags=["Root"])
async def get_version():
    """Version de l'API"""
    return {
        "version": settings.app_version,
        "app_name": settings.app_name
    }

@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Métriques Prometheus"""
    return generate_latest()

# Inclusion des routes API v1
app.include_router(api_router, prefix=settings.api_v1_prefix)

# Events
@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage"""
    logger.info(
        "application_startup",
        app_name=settings.app_name,
        version=settings.app_version
    )
    
    # Initialisation des moteurs OCR
    from .services.ocr_factory import get_ocr_factory
    factory = get_ocr_factory()
    logger.info(
        "engines_initialized",
        engines=factory.get_available_engines()
    )

@app.on_event("shutdown")
async def shutdown_event():
    """Nettoyage à l'arrêt"""
    logger.info("application_shutdown")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.debug
    )