"""Similarity schemas."""

from pydantic import BaseModel
from typing import Optional


class SimilarityResponse(BaseModel):
    """Similar ticker candidate."""
    symbol: str
    venue: str
    score: float
    explanation_cn: Optional[str] = None
    explanation_en: Optional[str] = None
    matched_features: dict
    current_price: Optional[float] = None

    class Config:
        from_attributes = True
