from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any

from app.auth.dependencies import verify_jwt
from app.services.validation_service import ValidationService
from app.services.ingestion_service import IngestionService
from app.config.settings import get_settings
from app.utils.logger import logger

settings = get_settings()

router = APIRouter(
    prefix="/api/v1",
    tags=["Administration Ingestion"]
)

ingestion_service = IngestionService()


@router.post("/ingest")
def ingest_school_data(
    records: List[Dict[str, Any]],
    user=Depends(verify_jwt)
):
    """
    Administration School Master Generic Ingestion API

    Flow

    State ERP
        ↓
    Generic Auth API
        ↓
    Verify JWT
        ↓
    Verify User (/auth/me)
        ↓
    State Validation
        ↓
    Duplicate Validation
        ↓
    Payload Validation
        ↓
    Table Mapper
        ↓
    Generic Bulk UPSERT
        ↓
    PostgreSQL
    """

    # =====================================================
    # Empty Payload
    # =====================================================

    if not records:
        raise HTTPException(
            status_code=400,
            detail="Payload cannot be empty."
        )

    # =====================================================
    # Max Payload Size
    # =====================================================

    if len(records) > settings.MAX_RECORDS_PER_REQUEST:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {settings.MAX_RECORDS_PER_REQUEST} records allowed."
        )

    # =====================================================
    # Payload Validation
    # =====================================================

    valid, errors = ValidationService.validate_payload(records)

    if not valid:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "failed",
                "validation_errors": errors
            }
        )

    # =====================================================
    # One State Per Request
    # =====================================================

    payload_states = {
        r.get("state_id")
        for r in records
    }

    if len(payload_states) != 1:
        raise HTTPException(
            status_code=400,
            detail="Payload contains multiple state_ids."
        )

    # =====================================================
    # Token State Validation
    # =====================================================

    authenticated_state = user["state_id"]

    payload_state = records[0].get("state_id")

    if str(authenticated_state) != str(payload_state):
        raise HTTPException(
            status_code=403,
            detail={
                "status": "failed",
                "message": "Authenticated state does not match payload state.",
                "authenticated_state": authenticated_state,
                "payload_state": payload_state
            }
        )

    # =====================================================
    # Database Ingestion
    # =====================================================

    try:

        summary = ingestion_service.ingest(records)

        return {

            "status": "success",

            "message": "Administration data ingested successfully.",

            "authenticated_user": {

                "username": user["username"],

                "state_id": user["state_id"]

            },

            "records_received": len(records),

            "tables_updated": summary

        }

    except Exception as ex:
        logger.exception(ex)

        raise HTTPException(

            status_code=500,

            detail={

                "status": "failed",

                "error": "Internal ingestion failure. Please contact support."

            }

        )


@router.get("/health")
def health():

    return {

        "status": "healthy",

        "service": "Administration Ingestion API"

    }
