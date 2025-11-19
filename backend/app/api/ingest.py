"""Ingest API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.ingest import IngestRequest, IngestResponse
from app.services.ingest import IngestService

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_transcript(
    request: IngestRequest,
    db: Session = Depends(get_db)
):
    """
    Ingest a transcript and generate draft playbook cards.

    **Process:**
    1. Detect language and segment text
    2. Extract entities (companies, commodities, etc.)
    3. Map entities to ticker symbols
    4. Generate draft cards with entry/exit/invalidators
    5. Translate to both CN/EN

    **Acceptance:**
    - Process 10k+ word lesson in < 60 seconds
    - ≥8 valid cards with tickers and triggers
    - ≥90% precision on ticker mapping
    """
    try:
        ingest_service = IngestService(db)
        result = ingest_service.ingest_transcript(
            text=request.text,
            expert_ref=request.expert_ref
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingest failed: {str(e)}")
