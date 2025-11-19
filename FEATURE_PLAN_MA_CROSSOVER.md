# Feature Plan: 60-Day MA Crossover & Slope Monitoring

## Overview

Monitor when the 60-day moving average crosses over with 2-hour candle charts for specific tickers, with automatic alerts when:
1. **Crossover occurs** (60-day MA crosses above/below current price or another indicator)
2. **Slope becomes positive** (60-day MA trend turns upward)

---

## Requirements Analysis

### What You Need

1. **Data**: 2-hour OHLC candles + daily data for 60-day MA
2. **Calculation**: 60-day simple moving average (SMA) or exponential moving average (EMA)
3. **Crossover Detection**: Price crosses 60-day MA or 60-day MA crosses another MA
4. **Slope Calculation**: Change in MA value over time (positive = uptrend)
5. **Alerts**: Real-time or near-real-time notifications when conditions met

### Technical Challenges

1. **2-hour candles** require intraday data (free sources have limitations)
2. **60-day MA** calculated from daily closes (not 2-hour candles)
3. **Real-time monitoring** needs continuous price updates
4. **Alert delivery** must be fast and reliable

---

## Research: Available Options

I've researched 6 different approaches, ranked from **BEST** to least suitable:

---

## ⭐ **OPTION 1: TradingView Webhooks + Custom Worker (RECOMMENDED)**

### Why This Is Best

- ✅ **Most reliable** - TradingView's charting is industry-standard
- ✅ **Real intraday data** - 2-hour candles available
- ✅ **Built-in alerts** - You define conditions, TV handles monitoring
- ✅ **Webhooks** - Sends HTTP POST to your server when alert fires
- ✅ **No coding crossover logic** - TradingView's Pine Script does it
- ✅ **Cost-effective** - Free for basic, $15-60/mo for Pro features
- ✅ **Scalable** - Can monitor 100s of tickers

### How It Works

```
1. User creates alert in TradingView:
   "Alert me when IONQ 60-day MA slope turns positive"

2. TradingView monitors 24/7

3. When condition met → TradingView sends webhook:
   POST https://yourdomain.com/api/tradingview-webhook
   {
     "ticker": "IONQ",
     "alert": "60-day MA slope positive",
     "price": 13.25,
     "time": "2025-01-19T14:30:00Z"
   }

4. Your backend receives webhook → sends alert to user (email/Slack/Telegram)
```

### Implementation Plan

#### Phase 1: Backend Webhook Endpoint (1-2 hours)

**File:** `backend/app/api/tradingview.py`

```python
from fastapi import APIRouter, Request, HTTPException
from app.services.alert_service import send_alert_notification

router = APIRouter()

@router.post("/tradingview-webhook")
async def tradingview_webhook(request: Request):
    """
    Receive alerts from TradingView.

    TradingView sends:
    {
      "ticker": "{{ticker}}",
      "exchange": "{{exchange}}",
      "price": {{close}},
      "ma60": {{ta.sma(close, 60)}},
      "slope": "positive",
      "alert_name": "{{alert_name}}",
      "time": "{{time}}"
    }
    """
    data = await request.json()

    # Validate webhook (optional: add secret key check)
    # if data.get("secret") != os.getenv("TRADINGVIEW_SECRET"):
    #     raise HTTPException(401, "Invalid secret")

    # Extract info
    ticker = data.get("ticker")
    price = data.get("price")
    alert_name = data.get("alert_name")
    slope = data.get("slope")

    # Send notification
    await send_alert_notification(
        ticker=ticker,
        alert_type="MA_CROSSOVER",
        message=f"{ticker}: 60-day MA {slope} at ${price}",
        channels=["email", "telegram"]
    )

    # Log to database
    log_tradingview_alert(data)

    return {"status": "received"}
```

**Add to** `backend/app/main.py`:
```python
from app.api import tradingview
app.include_router(tradingview.router, prefix="/api", tags=["tradingview"])
```

#### Phase 2: TradingView Setup (15 minutes per ticker)

**Step 1: Create Alert in TradingView**

```pine
// Pine Script for 60-day MA crossover + slope detection
//@version=5
indicator("60-day MA Monitor", overlay=true)

// Calculate 60-day MA
ma60 = ta.sma(close, 60)
plot(ma60, color=color.blue, linewidth=2, title="60-day MA")

// Calculate slope (difference between current and 5 periods ago)
slope = ma60 - ma60[5]
slopePositive = slope > 0

// Crossover detection
crossUp = ta.crossover(close, ma60)
crossDown = ta.crossunder(close, ma60)

// Alert conditions
alertcondition(crossUp, title="Price crossed above 60-day MA",
    message='{"ticker":"{{ticker}}", "alert":"cross_up", "price":{{close}}, "ma60":{{ma60}}}')

alertcondition(crossDown, title="Price crossed below 60-day MA",
    message='{"ticker":"{{ticker}}", "alert":"cross_down", "price":{{close}}, "ma60":{{ma60}}}')

alertcondition(slopePositive and not slopePositive[1], title="60-day MA slope turned positive",
    message='{"ticker":"{{ticker}}", "alert":"slope_positive", "price":{{close}}, "ma60":{{ma60}}, "slope":{{slope}}}')
```

**Step 2: Configure Webhook**

1. Click "Alert" button in TradingView
2. Select condition: "60-day MA slope turned positive"
3. In "Notifications" tab:
   - ✅ Webhook URL: `https://yourdomain.com/api/tradingview-webhook`
4. Click "Create"

**Step 3: Repeat for All Tickers**

- Can create 400 alerts with TradingView Pro ($60/mo)
- Alerts never expire
- Monitors 24/7 even when you're offline

#### Phase 3: Alert Notification Service (30 minutes)

**File:** `backend/app/services/alert_service.py`

```python
import os
from emails import Message
import httpx

async def send_alert_notification(ticker: str, alert_type: str, message: str, channels: list):
    """Send alert via multiple channels."""

    if "email" in channels:
        await send_email_alert(ticker, message)

    if "telegram" in channels:
        await send_telegram_alert(message)

    if "slack" in channels:
        await send_slack_alert(message)

async def send_email_alert(ticker: str, message: str):
    """Send email alert."""
    msg = Message(
        subject=f"🚨 MA Alert: {ticker}",
        mail_from=os.getenv("ALERT_FROM_EMAIL"),
        mail_to=["your-email@gmail.com"],
    )
    msg.html = f"""
    <h2>Moving Average Alert</h2>
    <p><strong>{message}</strong></p>
    <p>Time: {datetime.now()}</p>
    <a href="https://tradingview.com/chart/?symbol={ticker}">View Chart →</a>
    """

    smtp = {
        "host": os.getenv("SMTP_HOST"),
        "port": int(os.getenv("SMTP_PORT")),
        "user": os.getenv("SMTP_USER"),
        "password": os.getenv("SMTP_PASSWORD"),
        "tls": True
    }

    msg.send(**smtp)

async def send_telegram_alert(message: str):
    """Send Telegram alert."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        })
```

#### Phase 4: Dashboard Integration (1 hour)

Add a new page to manage MA monitoring:

**File:** `frontend/app/[locale]/ma-monitor/page.tsx`

```typescript
'use client'

export default function MAMonitorPage() {
  const [tickers, setTickers] = useState<string[]>([])
  const [alerts, setAlerts] = useState<MAAlert[]>([])

  return (
    <div>
      <h1>60-Day MA Monitor</h1>

      {/* Add Ticker Form */}
      <form onSubmit={handleAddTicker}>
        <input
          type="text"
          placeholder="Enter ticker (e.g., IONQ)"
        />
        <button>Add to Monitoring</button>
      </form>

      {/* Monitored Tickers */}
      <div>
        <h2>Monitored Tickers</h2>
        {tickers.map(ticker => (
          <TickerCard
            key={ticker}
            ticker={ticker}
            ma60Value={...}
            slope={...}
            onRemove={() => removeTicker(ticker)}
          />
        ))}
      </div>

      {/* Recent Alerts */}
      <div>
        <h2>Recent MA Alerts</h2>
        {alerts.map(alert => (
          <AlertCard alert={alert} />
        ))}
      </div>
    </div>
  )
}
```

### Total Implementation Time

- **Phase 1 (Backend):** 2 hours
- **Phase 2 (TradingView setup):** 15 min × 10 tickers = 2.5 hours
- **Phase 3 (Notifications):** 30 minutes
- **Phase 4 (Dashboard):** 1 hour

**Total: ~6 hours** for complete implementation

### Costs

- **TradingView Free:** 1 alert per ticker (limited)
- **TradingView Pro:** $15/mo - 20 alerts
- **TradingView Pro+:** $30/mo - 100 alerts
- **TradingView Premium:** $60/mo - 400 alerts

**Recommended:** Start with Pro+ ($30/mo) for 100 tickers

### Pros & Cons

✅ **Pros:**
- Most reliable (TradingView handles all monitoring)
- Real-time intraday data
- No need to code complex TA logic
- Scalable to 100s of tickers
- Professional-grade charting
- Built-in backtesting
- Mobile app alerts

❌ **Cons:**
- Costs $30-60/mo for meaningful coverage
- Requires manual setup per ticker
- Depends on 3rd-party service

---

## OPTION 2: Alpaca Markets API + Custom Worker

### Overview

Use Alpaca's free real-time data API + custom Python worker that calculates MA and detects crossovers.

### How It Works

```python
# Worker runs every 2 hours
import alpaca_trade_api as tradeapi

api = tradeapi.REST(API_KEY, API_SECRET, base_url='https://paper-api.alpaca.markets')

def check_ma_crossover(ticker):
    # Get 60 days of daily data
    bars = api.get_bars(ticker, '1Day', limit=60).df

    # Calculate 60-day MA
    bars['ma60'] = bars['close'].rolling(60).mean()

    # Calculate slope (last 5 days)
    slope = (bars['ma60'].iloc[-1] - bars['ma60'].iloc[-6]) / 5

    # Get current 2-hour candle
    current_bars = api.get_bars(ticker, '2Hour', limit=1).df
    current_price = current_bars['close'].iloc[-1]

    # Check crossover
    prev_price = bars['close'].iloc[-2]
    prev_ma = bars['ma60'].iloc[-2]
    current_ma = bars['ma60'].iloc[-1]

    if prev_price < prev_ma and current_price > current_ma:
        send_alert(f"{ticker} crossed above 60-day MA!")

    if slope > 0 and calculate_prev_slope() <= 0:
        send_alert(f"{ticker} 60-day MA slope turned positive!")
```

### Pros & Cons

✅ **Pros:**
- Completely free (Alpaca provides free real-time data)
- Full control over logic
- No monthly costs

❌ **Cons:**
- More coding required
- Need to handle edge cases
- Worker must run continuously
- Limited to US equities

---

## OPTION 3: yfinance + Scheduled Worker (Current Setup)

### Overview

Extend existing EOD worker to check MA crossovers using yfinance (free).

### Limitations

- ❌ **No 2-hour candles** - yfinance only has 1h max (limited history)
- ❌ **EOD data only** for reliable long-term use
- ✅ **Free**
- ⚠️ **Delayed alerts** (only checks once per day)

**Verdict:** Not suitable for your 2-hour candle requirement.

---

## OPTION 4: Paid Data Providers (Polygon.io, IEX Cloud)

### Overview

Professional data APIs with intraday candles.

### Costs

- **Polygon.io:** $29-250/mo depending on features
- **IEX Cloud:** $9-999/mo depending on usage
- **Alpha Vantage:** $50-500/mo

### Verdict

More expensive than TradingView, more work to implement.

---

## OPTION 5: Build Real-Time WebSocket Monitor

### Overview

Connect to real-time price streams, calculate MA in real-time.

### Pros & Cons

✅ **Pros:**
- Instant alerts
- Full control

❌ **Cons:**
- Very complex to build
- Expensive data feeds
- High infrastructure costs
- Requires 24/7 running server

**Verdict:** Overkill for this use case.

---

## OPTION 6: Manual Monitoring with Existing Tools

### Overview

Use existing tools like TradingView, set up manual checks.

### Verdict

Not automated - doesn't meet your requirement.

---

## ⭐ RECOMMENDED SOLUTION: Option 1 (TradingView Webhooks)

### Why TradingView Is Best

1. **Proven & Reliable:** Industry standard, used by millions
2. **Cost-Effective:** $30/mo for 100 tickers vs building from scratch
3. **Fast Implementation:** 6 hours total vs weeks for custom solution
4. **Professional Features:** Backtesting, screeners, mobile alerts
5. **Scalable:** Can easily add more tickers
6. **Maintenance-Free:** TradingView handles all data/monitoring

### Implementation Roadmap

**Week 1: Backend (2-3 hours)**
1. Create `/api/tradingview-webhook` endpoint
2. Build alert notification service (email/Telegram)
3. Add database logging for alerts
4. Test with sample webhook

**Week 2: TradingView Setup (2-3 hours)**
1. Subscribe to TradingView Pro+ ($30/mo)
2. Create Pine Script indicator
3. Set up alerts for initial 10-20 tickers
4. Configure webhook URLs
5. Test alerts

**Week 3: Dashboard (1-2 hours)**
1. Build MA Monitor page in frontend
2. Display active monitoring list
3. Show recent alerts
4. Add "Add Ticker" form

**Week 4: Polish & Scale**
1. Add more tickers
2. Fine-tune alert conditions
3. Add alert history/analytics
4. Document process

### Alternative: Hybrid Approach

**Free Tier (Start Here):**
- Use TradingView Free for top 5-10 most important tickers
- Use Alpaca API for remaining tickers (free, but more work)

**Upgrade Path:**
- If works well → upgrade to TradingView Pro+ for full coverage
- If need more than 100 tickers → consider Polygon.io

---

## Technical Specifications

### Database Schema Addition

```sql
CREATE TABLE ma_alert (
  id UUID PRIMARY KEY,
  ticker VARCHAR(10) NOT NULL,
  alert_type VARCHAR(50) NOT NULL,  -- 'cross_up', 'cross_down', 'slope_positive'
  price NUMERIC(10,2),
  ma60_value NUMERIC(10,2),
  slope NUMERIC(10,4),
  triggered_at TIMESTAMP DEFAULT NOW(),
  source VARCHAR(50) DEFAULT 'tradingview',
  raw_data JSONB,
  INDEX idx_ticker_time (ticker, triggered_at)
);

CREATE TABLE monitored_ticker (
  id UUID PRIMARY KEY,
  ticker VARCHAR(10) UNIQUE NOT NULL,
  enabled BOOLEAN DEFAULT TRUE,
  tradingview_alert_id VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW(),
  user_id UUID  -- for multi-user support
);
```

### API Endpoints

```
POST /api/tradingview-webhook
  - Receives webhooks from TradingView
  - Validates, processes, sends alerts

GET /api/ma-alerts?ticker={ticker}
  - Get recent MA alerts for a ticker

POST /api/ma-monitor/add
  - Add ticker to monitoring list
  - Returns TradingView setup instructions

DELETE /api/ma-monitor/{ticker}
  - Remove ticker from monitoring

GET /api/ma-monitor/tickers
  - List all monitored tickers with current MA values
```

---

## Next Steps

1. **Decision Point:** Choose TradingView approach?
2. **If yes:** I'll implement Phase 1 (backend webhook + notifications)
3. **If exploring alternatives:** Let me know which option interests you

**My recommendation:** Start with TradingView Free for 1-2 tickers as proof of concept, then upgrade if it works well.

Would you like me to proceed with implementing Option 1?
