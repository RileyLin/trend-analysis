"""Alert schemas."""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class AlertEnableRequest(BaseModel):
    """Request to enable alerts for a card."""
    card_id: str
    channels: List[str] = ["email"]  # email, slack, telegram


class AlertResponse(BaseModel):
    """Alert event response."""
    id: str
    trigger_id: str
    card_id: str
    fired_at: datetime
    symbol: str
    price: float
    reason: str
    reason_cn: Optional[str] = None
    reason_en: Optional[str] = None
    invalidator: str
    invalidator_cn: Optional[str] = None
    invalidator_en: Optional[str] = None

    class Config:
        from_attributes = True
