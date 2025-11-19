"""Portfolio schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import date
from decimal import Decimal


class PositionResponse(BaseModel):
    """Position response."""
    id: str
    symbol: str
    opened_at: date
    entry_px: Decimal
    closed_at: Optional[date]
    exit_px: Optional[Decimal]
    qty: Decimal
    card_id: str
    status: str
    current_px: Optional[Decimal] = None
    pnl: Optional[Decimal] = None
    pnl_pct: Optional[float] = None

    class Config:
        from_attributes = True


class PortfolioStats(BaseModel):
    """Portfolio statistics."""
    total_positions: int
    open_positions: int
    closed_positions: int
    total_pnl: Decimal
    total_pnl_pct: float
    win_rate: float
    max_drawdown: float
    twr: float  # Time-weighted return
    exposure_by_theme: dict
