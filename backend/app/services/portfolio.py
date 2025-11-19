"""Portfolio service - manage paper portfolio."""

from typing import List, Dict
from sqlalchemy.orm import Session
from datetime import date, datetime
from decimal import Decimal

from app.models.portfolio import Position
from app.schemas.portfolio import PositionResponse, PortfolioStats
from app.services.trigger_engine import TriggerEngine


class PortfolioService:
    """Manage paper portfolio positions."""

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
        self.trigger_engine = TriggerEngine(db)

    def open_position(
        self,
        symbol: str,
        entry_px: float,
        qty: float,
        card_id: str
    ) -> Position:
        """
        Open a new paper position.

        Args:
            symbol: Ticker symbol
            entry_px: Entry price
            qty: Quantity
            card_id: Card/thesis ID

        Returns: Position object
        """
        position = Position(
            symbol=symbol,
            opened_at=date.today(),
            entry_px=Decimal(str(entry_px)),
            qty=Decimal(str(qty)),
            card_id=card_id,
            status="open"
        )

        self.db.add(position)
        self.db.commit()
        self.db.refresh(position)

        return position

    def close_position(
        self,
        position_id: str,
        exit_px: float
    ) -> Position:
        """
        Close a position.

        Args:
            position_id: Position UUID
            exit_px: Exit price

        Returns: Updated position
        """
        position = self.db.query(Position).filter(Position.id == position_id).first()

        if not position:
            raise ValueError(f"Position {position_id} not found")

        position.closed_at = date.today()
        position.exit_px = Decimal(str(exit_px))
        position.status = "closed"

        self.db.commit()
        self.db.refresh(position)

        return position

    def get_all_positions(self, include_closed: bool = True) -> List[PositionResponse]:
        """Get all positions."""
        query = self.db.query(Position)

        if not include_closed:
            query = query.filter(Position.status == "open")

        positions = query.order_by(Position.opened_at.desc()).all()

        # Enrich with current prices and PnL
        position_responses = []

        for pos in positions:
            current_px = None
            pnl = None
            pnl_pct = None

            if pos.status == "open":
                # Get current price
                current_px = self.trigger_engine._get_current_price(pos.symbol)

                if current_px:
                    pnl = (Decimal(str(current_px)) - pos.entry_px) * pos.qty
                    pnl_pct = float(((Decimal(str(current_px)) - pos.entry_px) / pos.entry_px) * 100)
            else:
                # Closed position
                if pos.exit_px:
                    pnl = (pos.exit_px - pos.entry_px) * pos.qty
                    pnl_pct = float(((pos.exit_px - pos.entry_px) / pos.entry_px) * 100)

            position_responses.append(PositionResponse(
                id=str(pos.id),
                symbol=pos.symbol,
                opened_at=pos.opened_at,
                entry_px=pos.entry_px,
                closed_at=pos.closed_at,
                exit_px=pos.exit_px,
                qty=pos.qty,
                card_id=pos.card_id,
                status=pos.status,
                current_px=Decimal(str(current_px)) if current_px else None,
                pnl=pnl,
                pnl_pct=pnl_pct
            ))

        return position_responses

    def get_portfolio_stats(self) -> PortfolioStats:
        """Calculate portfolio statistics."""
        all_positions = self.get_all_positions(include_closed=True)

        total_positions = len(all_positions)
        open_positions = sum(1 for p in all_positions if p.status == "open")
        closed_positions = sum(1 for p in all_positions if p.status == "closed")

        # Calculate total PnL
        total_pnl = sum(p.pnl for p in all_positions if p.pnl)

        # Calculate win rate
        closed = [p for p in all_positions if p.status == "closed" and p.pnl is not None]
        winners = sum(1 for p in closed if p.pnl > 0)
        win_rate = (winners / len(closed) * 100) if closed else 0.0

        # Calculate max drawdown (simplified)
        pnl_pcts = [p.pnl_pct for p in all_positions if p.pnl_pct is not None]
        max_drawdown = min(pnl_pcts) if pnl_pcts else 0.0

        # Calculate total PnL %
        total_invested = sum(p.entry_px * p.qty for p in all_positions)
        total_pnl_pct = float((total_pnl / total_invested * 100)) if total_invested > 0 else 0.0

        # TWR (simplified - just average return)
        twr = sum(pnl_pcts) / len(pnl_pcts) if pnl_pcts else 0.0

        # Exposure by theme (placeholder)
        exposure_by_theme = {}

        return PortfolioStats(
            total_positions=total_positions,
            open_positions=open_positions,
            closed_positions=closed_positions,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
            win_rate=win_rate,
            max_drawdown=max_drawdown,
            twr=twr,
            exposure_by_theme=exposure_by_theme
        )
