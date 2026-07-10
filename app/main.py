from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.database.connection import (
    initialize_connection_pool,
    close_connection_pool
)
from app.utils.logger import logger

# Import Routers
from app.routers.administration import router as administration_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("=========================================")
    logger.info("Starting Administration Ingestion API")
    logger.info("=========================================")

    initialize_connection_pool()

    yield

    logger.info("Closing PostgreSQL Connection Pool...")
    close_connection_pool()

    logger.info("Administration API stopped successfully.")


app = FastAPI(

    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Administration Ingestion API

Receives Administration data from State ERP systems.

### Workflow

State ERP
↓
Generic Authentication API
↓
JWT Token
↓
Administration Ingestion API
↓
Validation
↓
Table Mapper
↓
Bulk UPSERT
↓
PostgreSQL
""",
    debug=settings.DEBUG and not settings.is_production,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_DOCS else None,
    openapi_url="/openapi.json" if settings.ENABLE_DOCS else None,
)

# -----------------------------
# CORS
# -----------------------------
cors_allowed_origins = settings.cors_allowed_origins

if cors_allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_allowed_origins,
        allow_credentials="*" not in cors_allowed_origins,
        allow_methods=["POST", "GET", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

# -----------------------------
# Routers
# -----------------------------
app.include_router(administration_router)

# -----------------------------
# Health Check
# -----------------------------
@app.get("/", tags=["Home"])
def home():
    return {
        "message": "Administration Ingestion API is running."
    }


@app.get("/health", tags=["Health"])
def health():

    return {
        "status": "healthy",
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/ready", tags=["Health"])
def readiness():
    from app.database.connection import get_connection, release_connection

    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        connection.rollback()

        return {
            "status": "ready",
            "database": "available"
        }

    except Exception as ex:
        if connection is not None:
            connection.rollback()
        logger.exception(ex)
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "database": "unavailable"
            }
        )

    finally:
        if connection is not None:
            release_connection(connection)
