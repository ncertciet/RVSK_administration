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
        Validate all records
            ↓
        ┌─────────────────────────────┐
        │                             │
        ▼                             ▼
    Valid Records               Invalid Records
        │                             │
        ▼                             ▼
      Mapper                  UDISE + Errors
        │
        ▼
    Bulk UPSERT
        │
        ▼
    PostgreSQL
        │
        ▼
    Processing Response
    """

    # ==========================================================
    # EMPTY PAYLOAD
    # ==========================================================

    if not records:

        raise HTTPException(
            status_code=400,
            detail={
                "status": "failed",
                "message": "Payload cannot be empty."
            }
        )

    # ==========================================================
    # MAX PAYLOAD SIZE
    # ==========================================================

    if len(records) > settings.MAX_RECORDS_PER_REQUEST:

        raise HTTPException(
            status_code=400,
            detail={
                "status": "failed",
                "message": (
                    f"Maximum "
                    f"{settings.MAX_RECORDS_PER_REQUEST} "
                    f"records allowed."
                )
            }
        )

    # ==========================================================
    # VALIDATE PAYLOAD
    # ==========================================================

    try:

        validation_result = (
            ValidationService.validate_payload(records)
        )

    except Exception as ex:

        logger.exception(ex)

        raise HTTPException(
            status_code=500,
            detail={
                "status": "failed",
                "message": "Validation service failed."
            }
        )

    # ==========================================================
    # EXPECTED VALIDATION RESULT
    #
    # valid_records
    # failed_records
    # ==========================================================

    valid_records = validation_result["valid_records"]

    failed_records = validation_result["failed_records"]

    # ==========================================================
    # STATE VALIDATION
    #
    # Validate state_id from school_profile
    # ==========================================================

    payload_states = set()

    for record in records:

        school_profile = record.get(
            "school_profile",
            {}
        )

        if isinstance(school_profile, dict):

            state_id = school_profile.get(
                "state_id"
            )

            if state_id is not None:
                payload_states.add(
                    str(state_id)
                )

    # ==========================================================
    # MULTIPLE STATE VALIDATION
    # ==========================================================

    if len(payload_states) != 1:

        raise HTTPException(
            status_code=400,
            detail={
                "status": "failed",
                "message": (
                    "Payload must contain "
                    "exactly one state_id."
                ),
                "payload_states": list(payload_states)
            }
        )

    payload_state = next(
        iter(payload_states)
    )

    # ==========================================================
    # TOKEN STATE VALIDATION
    # ==========================================================

    authenticated_state = str(
        user["state_id"]
    )

    if authenticated_state != payload_state:

        raise HTTPException(
            status_code=403,
            detail={
                "status": "failed",
                "message": (
                    "Authenticated state does not "
                    "match payload state."
                ),
                "authenticated_state": (
                    user["state_id"]
                ),
                "payload_state": payload_state
            }
        )

    # ==========================================================
    # NO VALID RECORDS
    # ==========================================================

    if not valid_records:

        return {
            "status": "failed",
            "message": (
                "All records failed validation. "
                "No data was inserted."
            ),

            "records_received": len(records),

            "records_valid": 0,

            "records_failed": len(
                failed_records
            ),

            "records_ingested": 0,

            "authenticated_user": {
                "username": user["username"],
                "state_id": user["state_id"]
            },

            "tables_updated": {},

            "failed_records": failed_records
        }

    # ==========================================================
    # DATABASE INGESTION
    # ONLY VALID RECORDS ARE SENT
    # ==========================================================

    try:

        summary = ingestion_service.ingest(
            valid_records
        )

        # ======================================================
        # FINAL RESPONSE
        # ======================================================

        if failed_records:

            status = "completed_with_errors"

            message = (
                "Administration data processed "
                "with validation errors."
            )

        else:

            status = "success"

            message = (
                "Administration data ingested "
                "successfully."
            )

        return {

            "status": status,

            "message": message,

            "authenticated_user": {

                "username": user["username"],

                "state_id": user["state_id"]

            },

            "records_received": len(records),

            "records_valid": len(valid_records),

            "records_failed": len(
                failed_records
            ),

            "records_ingested": len(valid_records),

            "tables_updated": summary,

            "failed_records": failed_records

        }

    except Exception as ex:

        logger.exception(ex)

        raise HTTPException(

            status_code=500,

            detail={

                "status": "failed",

                "message": (
                    "Internal ingestion failure. "
                    "No valid records were processed."
                ),

                "error": (
                    "Please contact support."
                )

            }
        )


# ==============================================================
# HEALTH
# ==============================================================

@router.get("/health")
def health():

    return {

        "status": "healthy",

        "service": (
            "Administration Ingestion API"
        )

    }