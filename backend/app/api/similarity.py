"""Similarity/Discovery API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.schemas.similarity import SimilarityResponse
from app.services.discovery import DiscoveryEngine
from app.models.similarity import SimilarityCandidate

router = APIRouter()


@router.get("/cards/{card_id}/similar", response_model=List[SimilarityResponse])
async def get_similar_tickers(
    card_id: str,
    top_k: int = Query(10, ge=1, le=50),
    min_score: float = Query(0.5, ge=0.0, le=1.0),
    db: Session = Depends(get_db)
):
    """
    Get similar tickers for a card using the discovery engine.

    **Discovery Logic:**
    1. Extract card features (themes, catalysts, geo, text)
    2. Generate multilingual embeddings
    3. Score candidate instruments by similarity
    4. Return top matches with explainability

    **Acceptance:**
    - ≥3 reasonable candidates per card (SME review)
    - Every candidate has explainability path
    """
    # Check if candidates already cached
    existing_candidates = db.query(SimilarityCandidate).filter(
        SimilarityCandidate.card_id == card_id,
        SimilarityCandidate.score >= min_score
    ).order_by(SimilarityCandidate.score.desc()).limit(top_k).all()

    if existing_candidates:
        # Return cached results
        return [
            SimilarityResponse(
                symbol=c.candidate_symbol,
                venue="",  # TODO: Get from instrument
                score=c.score,
                explanation_cn=c.explanation_cn,
                explanation_en=c.explanation_en,
                matched_features={},
                current_price=None
            )
            for c in existing_candidates
        ]

    # Generate new candidates
    discovery_engine = DiscoveryEngine(db)

    try:
        candidates = discovery_engine.find_similar_tickers(
            card_id=card_id,
            top_k=top_k,
            min_score=min_score
        )

        return [
            SimilarityResponse(
                symbol=c.candidate_symbol,
                venue="",
                score=c.score,
                explanation_cn=c.explanation_cn,
                explanation_en=c.explanation_en,
                matched_features={},
                current_price=None
            )
            for c in candidates
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to find similar tickers: {str(e)}"
        )
