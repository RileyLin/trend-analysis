"""Portfolio API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.schemas.portfolio import PositionResponse, PortfolioStats
from app.services.portfolio import PortfolioService

router = APIRouter()


@router.get("/portfolio", response_model=List[PositionResponse])
async def get_portfolio(
    include_closed: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get paper portfolio positions.

    Returns all positions with current prices and PnL calculations.
    """
    portfolio_service = PortfolioService(db)
    positions = portfolio_service.get_all_positions(include_closed=include_closed)

    return positions


@router.get("/portfolio/stats", response_model=PortfolioStats)
async def get_portfolio_stats(
    db: Session = Depends(get_db)
):
    """
    Get portfolio statistics.

    Includes:
    - Total/open/closed positions
    - Total PnL and PnL %
    - Win rate
    - Max drawdown
    - TWR (time-weighted return)
    - Exposure by theme
    """
    portfolio_service = PortfolioService(db)
    stats = portfolio_service.get_portfolio_stats()

    return stats


@router.post("/portfolio/positions")
async def open_position(
    symbol: str,
    entry_px: float,
    qty: float,
    card_id: str,
    db: Session = Depends(get_db)
):
    """Open a new paper position."""
    portfolio_service = PortfolioService(db)

    try:
        position = portfolio_service.open_position(
            symbol=symbol,
            entry_px=entry_px,
            qty=qty,
            card_id=card_id
        )

        return {
            "message": "Position opened",
            "position_id": str(position.id),
            "symbol": symbol,
            "entry_px": float(position.entry_px),
            "qty": float(position.qty)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open position: {str(e)}")


@router.put("/portfolio/positions/{position_id}/close")
async def close_position(
    position_id: str,
    exit_px: float,
    db: Session = Depends(get_db)
):
    """Close a position."""
    portfolio_service = PortfolioService(db)

    try:
        position = portfolio_service.close_position(
            position_id=position_id,
            exit_px=exit_px
        )

        # Calculate PnL
        pnl = (position.exit_px - position.entry_px) * position.qty
        pnl_pct = float(((position.exit_px - position.entry_px) / position.entry_px) * 100)

        return {
            "message": "Position closed",
            "position_id": str(position.id),
            "symbol": position.symbol,
            "pnl": float(pnl),
            "pnl_pct": pnl_pct
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to close position: {str(e)}")
