"""EOD trigger evaluation worker."""

import time
from datetime import datetime
from sqlalchemy.orm import Session
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db.database import SessionLocal
from app.services.trigger_engine import TriggerEngine


def run_eod_trigger_evaluation():
    """
    Run end-of-day trigger evaluation.

    This function:
    1. Evaluates all active triggers
    2. Generates alerts for fired triggers
    3. Sends notifications (email/webhook)
    4. Auto-enters paper trades if configured
    """
    print(f"[{datetime.now()}] Starting EOD trigger evaluation...")

    db: Session = SessionLocal()

    try:
        trigger_engine = TriggerEngine(db)

        # Evaluate all triggers
        alerts = trigger_engine.evaluate_all_triggers()

        print(f"[{datetime.now()}] Evaluated triggers, generated {len(alerts)} alerts")

        # TODO: Send notifications (email, Slack, Telegram)
        for alert in alerts:
            payload = alert.payload or {}
            print(f"  Alert: {payload.get('reason', 'Unknown reason')}")

            # TODO: Auto-enter paper position if user opted in
            # portfolio_service.open_position(...)

        print(f"[{datetime.now()}] EOD trigger evaluation complete")

    except Exception as e:
        print(f"[{datetime.now()}] Error in EOD trigger evaluation: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


def start_scheduler():
    """Start the scheduler for EOD trigger evaluation."""
    scheduler = BlockingScheduler()

    # Run every day at 22:00 (10 PM) - after market close
    scheduler.add_job(
        run_eod_trigger_evaluation,
        trigger=CronTrigger(hour=22, minute=0),
        id='eod_trigger_evaluation',
        name='EOD Trigger Evaluation',
        replace_existing=True
    )

    print("Starting EOD trigger evaluation scheduler...")
    print("Scheduled to run daily at 22:00")

    # For testing, also run immediately on startup
    run_eod_trigger_evaluation()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Shutting down scheduler...")
        scheduler.shutdown()


if __name__ == "__main__":
    start_scheduler()
