"""Ingest request/response schemas."""

from pydantic import BaseModel
from typing import List, Optional
from .card import CardCreate


class IngestRequest(BaseModel):
    """Request to ingest a transcript."""
    text: str
    expert_ref: Optional[str] = None
    locale: str = "zh-CN"  # Default to Chinese


class EntityCandidate(BaseModel):
    """Entity extraction candidate."""
    text: str
    type: str  # Company, Commodity, Exchange, Country, Instrument, Policy_Actor, Rating_Agency
    confidence: float
    ticker_candidates: List[dict] = []


class DraftCard(CardCreate):
    """Draft card with extraction metadata."""
    extraction_confidence: float
    entities: List[EntityCandidate] = []


class IngestResponse(BaseModel):
    """Response from ingest endpoint."""
    cards: List[DraftCard]
    processing_time: float
    total_entities_extracted: int
    language_detected: str
