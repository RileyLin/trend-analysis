"""Card API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.schemas.card import CardCreate, CardUpdate, CardResponse
from app.models.thesis import Thesis, ThesisInstrument, QuoteRef
from app.models.trigger import TriggerRule, InvalidatorRule
from app.models.instrument import Instrument

router = APIRouter()


@router.post("/cards", response_model=CardResponse, status_code=201)
async def create_card(
    card: CardCreate,
    db: Session = Depends(get_db)
):
    """Create a new playbook card."""
    try:
        # Create thesis
        thesis = Thesis(
            id=card.id,
            asof=card.asof,
            statement="",  # Placeholder
            horizon=card.horizon,
            conviction=card.confidence,
            summary_cn=card.summary_cn,
            summary_en=card.summary_en,
            direction=card.direction
        )

        db.add(thesis)

        # Add instruments
        for inst_ref in card.instruments:
            # Get or create instrument
            instrument = db.query(Instrument).filter(
                Instrument.symbol == inst_ref.symbol,
                Instrument.venue == inst_ref.venue
            ).first()

            if not instrument:
                instrument = Instrument(
                    id=f"{inst_ref.symbol}:{inst_ref.venue}",
                    symbol=inst_ref.symbol,
                    venue=inst_ref.venue,
                    asset_class="equity",
                    display_name_en=inst_ref.display_name_en,
                    display_name_cn=inst_ref.display_name_cn
                )
                db.add(instrument)

            # Link to thesis
            thesis_inst = ThesisInstrument(
                thesis_id=thesis.id,
                instrument_id=instrument.id,
                role=inst_ref.role
            )
            db.add(thesis_inst)

        # Add quotes
        for quote_ref in card.why:
            quote = QuoteRef(
                thesis_id=thesis.id,
                quote=quote_ref.quote,
                source_loc=quote_ref.source_loc,
                gloss_cn=quote_ref.gloss_cn,
                gloss_en=quote_ref.gloss_en
            )
            db.add(quote)

        # Add triggers
        for trigger_expr in card.entry_triggers:
            trigger = TriggerRule(
                thesis_id=thesis.id,
                kind=trigger_expr.type,
                expr=trigger_expr.expr,
                nl_cn=trigger_expr.nl_cn,
                nl_en=trigger_expr.nl_en
            )
            db.add(trigger)

        # Add invalidators
        for inv_expr in card.invalidators:
            invalidator = InvalidatorRule(
                thesis_id=thesis.id,
                kind=inv_expr.type,
                expr=inv_expr.expr,
                nl_cn=inv_expr.nl_cn,
                nl_en=inv_expr.nl_en
            )
            db.add(invalidator)

        db.commit()
        db.refresh(thesis)

        return thesis

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create card: {str(e)}")


@router.get("/cards", response_model=List[CardResponse])
async def list_cards(
    week: Optional[str] = Query(None, description="Week filter (YYYY-Www)"),
    db: Session = Depends(get_db)
):
    """List playbook cards."""
    query = db.query(Thesis)

    if week:
        # Parse week (simple approach)
        # Format: YYYY-Www (e.g., 2025-W46)
        # For MVP, just filter by date range
        pass

    cards = query.order_by(Thesis.asof.desc()).limit(100).all()

    return cards


@router.get("/cards/{card_id}", response_model=CardResponse)
async def get_card(
    card_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific card."""
    card = db.query(Thesis).filter(Thesis.id == card_id).first()

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    return card


@router.put("/cards/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: str,
    update: CardUpdate,
    db: Session = Depends(get_db)
):
    """Update a card."""
    card = db.query(Thesis).filter(Thesis.id == card_id).first()

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Update fields
    if update.summary_cn is not None:
        card.summary_cn = update.summary_cn

    if update.summary_en is not None:
        card.summary_en = update.summary_en

    if update.direction is not None:
        card.direction = update.direction

    if update.horizon is not None:
        card.horizon = update.horizon

    if update.confidence is not None:
        card.conviction = update.confidence

    db.commit()
    db.refresh(card)

    return card


@router.delete("/cards/{card_id}", status_code=204)
async def delete_card(
    card_id: str,
    db: Session = Depends(get_db)
):
    """Delete a card."""
    card = db.query(Thesis).filter(Thesis.id == card_id).first()

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    db.delete(card)
    db.commit()

    return None
