"""Trigger evaluation engine."""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import yfinance as yf

from app.models.trigger import TriggerRule
from app.models.alert import AlertEvent


class TriggerEngine:
    """Evaluate triggers and generate alerts."""

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
        self.price_cache = {}

    def evaluate_all_triggers(self) -> List[AlertEvent]:
        """
        Evaluate all active triggers against current market data.

        Returns: List of generated alert events
        """
        # Get all active triggers
        active_triggers = self.db.query(TriggerRule).filter(
            TriggerRule.status == "active"
        ).all()

        alerts = []

        for trigger in active_triggers:
            alert = self.evaluate_trigger(trigger)
            if alert:
                alerts.append(alert)

        return alerts

    def evaluate_trigger(self, trigger: TriggerRule) -> Optional[AlertEvent]:
        """
        Evaluate a single trigger.

        Returns: AlertEvent if triggered, None otherwise
        """
        if trigger.kind == "price_level":
            return self._evaluate_price_level(trigger)
        elif trigger.kind == "drawdown_pct":
            return self._evaluate_drawdown(trigger)
        elif trigger.kind == "ma_cross":
            return self._evaluate_ma_cross(trigger)
        elif trigger.kind == "time_stop":
            return self._evaluate_time_stop(trigger)
        elif trigger.kind == "event":
            # Event triggers are manual
            return None
        else:
            return None

    def _evaluate_price_level(self, trigger: TriggerRule) -> Optional[AlertEvent]:
        """Evaluate price level trigger."""
        expr = trigger.expr
        symbol = expr.get('symbol')
        op = expr.get('op')  # '>=', '<=', '>', '<'
        level = expr.get('level')

        if not all([symbol, op, level]):
            return None

        # Get current price
        current_price = self._get_current_price(symbol)
        if current_price is None:
            return None

        # Evaluate condition
        triggered = False

        if op == '>=' and current_price >= level:
            triggered = True
        elif op == '<=' and current_price <= level:
            triggered = True
        elif op == '>' and current_price > level:
            triggered = True
        elif op == '<' and current_price < level:
            triggered = True

        if triggered:
            # Create alert event
            alert = AlertEvent(
                trigger_id=trigger.id,
                payload={
                    'symbol': symbol,
                    'current_price': current_price,
                    'trigger_level': level,
                    'trigger_op': op,
                    'reason': f'{symbol} crossed {op} {level}',
                    'card_id': trigger.thesis_id,
                    'trigger_type': 'price_level'
                }
            )

            # Update trigger status
            trigger.status = "fired"

            self.db.add(alert)
            self.db.commit()

            return alert

        return None

    def _evaluate_drawdown(self, trigger: TriggerRule) -> Optional[AlertEvent]:
        """Evaluate drawdown percentage trigger."""
        expr = trigger.expr
        symbol = expr.get('symbol')
        pct = expr.get('pct')  # e.g., 5 for 5%
        window_days = expr.get('window_days', 20)

        if not all([symbol, pct]):
            return None

        # Get price history
        prices = self._get_price_history(symbol, days=window_days)
        if not prices:
            return None

        # Calculate high and current price
        high_price = max(prices)
        current_price = prices[-1]

        # Calculate drawdown
        drawdown_pct = ((current_price - high_price) / high_price) * 100

        if drawdown_pct <= -pct:
            # Triggered
            alert = AlertEvent(
                trigger_id=trigger.id,
                payload={
                    'symbol': symbol,
                    'current_price': current_price,
                    'high_price': high_price,
                    'drawdown_pct': drawdown_pct,
                    'reason': f'{symbol} down {abs(drawdown_pct):.1f}% from {window_days}D high',
                    'card_id': trigger.thesis_id,
                    'trigger_type': 'drawdown_pct'
                }
            )

            trigger.status = "fired"

            self.db.add(alert)
            self.db.commit()

            return alert

        return None

    def _evaluate_ma_cross(self, trigger: TriggerRule) -> Optional[AlertEvent]:
        """Evaluate moving average crossover trigger."""
        expr = trigger.expr
        symbol = expr.get('symbol')
        short_window = expr.get('short_window', 10)
        long_window = expr.get('long_window', 50)
        direction = expr.get('direction', 'up')  # 'up' or 'down'

        if not symbol:
            return None

        # Get price history
        prices = self._get_price_history(symbol, days=long_window + 5)
        if len(prices) < long_window:
            return None

        # Calculate MAs
        short_ma = sum(prices[-short_window:]) / short_window
        long_ma = sum(prices[-long_window:]) / long_window

        # Previous day MAs
        prev_short_ma = sum(prices[-(short_window+1):-1]) / short_window
        prev_long_ma = sum(prices[-(long_window+1):-1]) / long_window

        # Check for crossover
        triggered = False

        if direction == 'up':
            # Short MA crosses above long MA
            if prev_short_ma <= prev_long_ma and short_ma > long_ma:
                triggered = True
        elif direction == 'down':
            # Short MA crosses below long MA
            if prev_short_ma >= prev_long_ma and short_ma < long_ma:
                triggered = True

        if triggered:
            alert = AlertEvent(
                trigger_id=trigger.id,
                payload={
                    'symbol': symbol,
                    'current_price': prices[-1],
                    'short_ma': short_ma,
                    'long_ma': long_ma,
                    'reason': f'{symbol} {short_window}D MA crossed {direction} {long_window}D MA',
                    'card_id': trigger.thesis_id,
                    'trigger_type': 'ma_cross'
                }
            )

            trigger.status = "fired"

            self.db.add(alert)
            self.db.commit()

            return alert

        return None

    def _evaluate_time_stop(self, trigger: TriggerRule) -> Optional[AlertEvent]:
        """Evaluate time-based stop trigger."""
        expr = trigger.expr
        days = expr.get('days')

        if not days:
            return None

        # Get thesis creation date (from trigger's thesis)
        thesis = trigger.thesis

        if not thesis:
            return None

        # Calculate elapsed days
        elapsed_days = (datetime.now().date() - thesis.asof).days

        if elapsed_days >= days:
            alert = AlertEvent(
                trigger_id=trigger.id,
                payload={
                    'reason': f'Time stop triggered after {elapsed_days} days',
                    'card_id': trigger.thesis_id,
                    'trigger_type': 'time_stop',
                    'elapsed_days': elapsed_days,
                    'threshold_days': days
                }
            )

            trigger.status = "fired"

            self.db.add(alert)
            self.db.commit()

            return alert

        return None

    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol."""
        # Check cache first
        if symbol in self.price_cache:
            cached_price, cached_time = self.price_cache[symbol]
            if (datetime.now() - cached_time).seconds < 300:  # 5 min cache
                return cached_price

        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")

            if data.empty:
                return None

            current_price = float(data['Close'].iloc[-1])

            # Cache it
            self.price_cache[symbol] = (current_price, datetime.now())

            return current_price
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return None

    def _get_price_history(self, symbol: str, days: int = 20) -> List[float]:
        """Get price history for a symbol."""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=f"{days}d")

            if data.empty:
                return []

            return data['Close'].tolist()
        except Exception as e:
            print(f"Error fetching price history for {symbol}: {e}")
            return []
