"""Alerts API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.schemas.alert import AlertEnableRequest, AlertResponse
from app.models.alert import AlertEvent
from app.models.trigger import TriggerRule

router = APIRouter()


@router.post("/alerts/enable")
async def enable_alerts(
    request: AlertEnableRequest,
    db: Session = Depends(get_db)
):
    """
    Enable alerts for a card.

    This sets up monitoring for entry triggers and sends notifications
    when they fire via specified channels (email, slack, telegram).
    """
    # In a production system, this would:
    # 1. Store user's alert preferences
    # 2. Subscribe them to notifications
    # 3. Configure webhook/email settings

    # For MVP, just verify the card exists
    from app.models.thesis import Thesis

    card = db.query(Thesis).filter(Thesis.id == request.card_id).first()

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Check if card has active triggers
    active_triggers = db.query(TriggerRule).filter(
        TriggerRule.thesis_id == request.card_id,
        TriggerRule.status == "active"
    ).count()

    return {
        "message": f"Alerts enabled for card {request.card_id}",
        "channels": request.channels,
        "active_triggers": active_triggers
    }


@router.get("/alerts", response_model=List[AlertResponse])
async def list_alerts(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List recent alert events."""
    alerts = db.query(AlertEvent).order_by(
        AlertEvent.fired_at.desc()
    ).limit(limit).all()

    # Transform to response format
    alert_responses = []

    for alert in alerts:
        trigger = alert.trigger
        payload = alert.payload or {}

        alert_response = AlertResponse(
            id=str(alert.id),
            trigger_id=str(alert.trigger_id),
            card_id=trigger.thesis_id,
            fired_at=alert.fired_at,
            symbol=payload.get('symbol', ''),
            price=payload.get('current_price', 0.0),
            reason=payload.get('reason', ''),
            reason_cn=trigger.nl_cn,
            reason_en=trigger.nl_en,
            invalidator='',  # TODO: Get invalidator from thesis
            invalidator_cn='',
            invalidator_en=''
        )

        alert_responses.append(alert_response)

    return alert_responses


@router.post("/event/placeholder")
async def trigger_event_placeholder(
    card_id: str,
    event_type: str,
    db: Session = Depends(get_db)
):
    """
    Manually trigger an event placeholder.

    Used for policy/rating/margin events that can't be automatically detected.
    """
    # Find event triggers for this card
    event_triggers = db.query(TriggerRule).filter(
        TriggerRule.thesis_id == card_id,
        TriggerRule.kind == "event",
        TriggerRule.status == "active"
    ).all()

    triggered_count = 0

    for trigger in event_triggers:
        # Check if event matches
        expr = trigger.expr or {}

        if expr.get('kind') == event_type:
            # Create alert
            alert = AlertEvent(
                trigger_id=trigger.id,
                payload={
                    'event_type': event_type,
                    'reason': f'Manual event trigger: {event_type}',
                    'card_id': card_id,
                    'trigger_type': 'event'
                }
            )

            trigger.status = "fired"

            db.add(alert)
            triggered_count += 1

    db.commit()

    return {
        "message": f"Triggered {triggered_count} event(s)",
        "event_type": event_type,
        "card_id": card_id
    }
