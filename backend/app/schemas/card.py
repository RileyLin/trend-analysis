"""Card/Thesis schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date


class InstrumentRef(BaseModel):
    """Instrument reference in a card."""
    symbol: str
    venue: str
    role: str = "primary"  # primary, proxy, hedge
    display_name_en: Optional[str] = None
    display_name_cn: Optional[str] = None


class TriggerExpr(BaseModel):
    """Trigger expression."""
    type: str  # price_level, drawdown_pct, ma_cross, time_stop, event
    expr: Dict[str, Any]
    nl_cn: Optional[str] = None
    nl_en: Optional[str] = None


class QuoteReference(BaseModel):
    """Quote reference."""
    quote: str
    source_loc: Optional[str] = None
    gloss_cn: Optional[str] = None
    gloss_en: Optional[str] = None


class CardCreate(BaseModel):
    """Create a new card."""
    id: str
    asof: date
    summary_cn: Optional[str] = None
    summary_en: Optional[str] = None
    direction: str  # long, short, avoid
    horizon: str  # 1w, 1m, 3m, 6m
    instruments: List[InstrumentRef]
    entry_triggers: List[TriggerExpr]
    invalidators: List[TriggerExpr]
    catalysts: List[str] = []
    risks: List[str] = []
    why: List[QuoteReference] = []
    confidence: float = Field(ge=0.0, le=1.0)


class CardUpdate(BaseModel):
    """Update an existing card."""
    summary_cn: Optional[str] = None
    summary_en: Optional[str] = None
    direction: Optional[str] = None
    horizon: Optional[str] = None
    instruments: Optional[List[InstrumentRef]] = None
    entry_triggers: Optional[List[TriggerExpr]] = None
    invalidators: Optional[List[TriggerExpr]] = None
    catalysts: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    why: Optional[List[QuoteReference]] = None
    confidence: Optional[float] = None


class CardResponse(BaseModel):
    """Card response."""
    id: str
    asof: date
    summary_cn: Optional[str]
    summary_en: Optional[str]
    direction: str
    horizon: str
    instruments: List[InstrumentRef]
    entry_triggers: List[TriggerExpr]
    invalidators: List[TriggerExpr]
    catalysts: List[str]
    risks: List[str]
    why: List[QuoteReference]
    confidence: float

    class Config:
        from_attributes = True


class PlaybookCard(CardResponse):
    """Extended card for playbook view with similar tickers."""
    similar_count: int = 0
