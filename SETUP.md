# Setup Guide - Thesis → Ticker Engine

## Quick Start (Docker)

The fastest way to get started:

```bash
# 1. Clone the repo and navigate to it
cd trend-analysis

# 2. Copy environment file
cp .env.example .env

# 3. Start everything with Docker Compose
docker-compose up

# 4. In another terminal, initialize the database
docker-compose exec backend python scripts/init_db.py
docker-compose exec backend python scripts/seed_glossary.py
docker-compose exec backend python scripts/seed_instruments.py

# 5. Access the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

## Development Setup (Without Docker)

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with pgvector extension

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
# 1. Create PostgreSQL database
createdb thesis_ticker_engine

# 2. Enable pgvector extension
psql thesis_ticker_engine -c "CREATE EXTENSION vector;"

# 3. Initialize tables
python scripts/init_db.py

# 4. Seed data
python scripts/seed_glossary.py
python scripts/seed_instruments.py

# 5. Run the server
uvicorn app.main:app --reload
```

Backend will be available at http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at http://localhost:3000

## Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v --cov=app
```

### End-to-End Test

Make sure both backend and frontend are running, then:

```bash
cd backend
python scripts/test_e2e.py
```

This will:
1. Ingest a sample bilingual transcript
2. Generate playbook cards
3. Test all API endpoints
4. Verify bilingual functionality

## Usage

### 1. Ingest a Transcript

Navigate to the **Ingest** page:
- Paste your weekly lesson transcript (supports CN/EN mixed content)
- Click "Extract Cards"
- Review the generated draft cards
- Save cards to your playbook

**Acceptance Criteria:**
- ✅ 10k+ word lessons processed in < 60 seconds
- ✅ ≥8 valid cards with tickers and triggers
- ✅ ≥90% precision on ticker mapping

### 2. View Playbook

Navigate to the **Playbook** page:
- See all your tradable cards
- View entry triggers and invalidators
- Enable alerts for specific cards
- Explore similar tickers with explainability

### 3. Monitor Alerts

Navigate to the **Alerts** page:
- View triggered entry conditions
- Add positions to paper portfolio
- See bilingual explanations

### 4. Track Performance

Navigate to the **Scoreboard** page:
- View paper portfolio P&L
- See win rate and max drawdown
- Monitor all positions (open/closed)

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

**Database:**
- `DATABASE_URL` - PostgreSQL connection string

**API:**
- `API_HOST` - API host (default: 0.0.0.0)
- `API_PORT` - API port (default: 8000)

**NLP:**
- `EMBEDDING_MODEL` - Multilingual embedding model (default: intfloat/multilingual-e5-base)

**Alerts:**
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` - Email configuration
- `SLACK_WEBHOOK_URL` - Slack webhook for alerts
- `TELEGRAM_BOT_TOKEN` - Telegram bot token

**Data:**
- `PRICE_DATA_SOURCE` - Price data source (default: yfinance)
- `EOD_UPDATE_HOUR` - Hour to run EOD worker (default: 22)

## Architecture

### Backend (FastAPI)

```
backend/
├── app/
│   ├── api/           # API routes
│   ├── models/        # SQLAlchemy models
│   ├── services/      # Business logic
│   │   ├── ingest.py          # Transcript processing
│   │   ├── ner.py             # Entity extraction
│   │   ├── ticker_mapper.py   # Ticker mapping
│   │   ├── translation.py     # Bilingual translation
│   │   ├── trigger_engine.py  # Trigger evaluation
│   │   ├── discovery.py       # Similar-logic engine
│   │   └── portfolio.py       # Portfolio management
│   ├── db/            # Database utilities
│   └── workers/       # Background jobs
├── tests/             # Unit tests
└── scripts/           # Utilities
```

### Frontend (Next.js)

```
frontend/
├── app/
│   └── [locale]/      # i18n routing
│       ├── ingest/    # Ingest page
│       ├── playbook/  # Playbook page
│       ├── alerts/    # Alerts page
│       └── scoreboard/# Portfolio page
├── components/        # React components
└── lib/
    ├── api.ts         # API client
    └── translations.ts# i18n translations
```

## Key Features

### ✅ Bilingual (CN/EN) Support
- Auto-detect language per chunk
- Glossary-based translation
- Field-level bilingualism (all text stored in both languages)
- No loss of meaning in translation

### ✅ Entity Extraction
- Companies, commodities, exchanges, countries, policy actors, rating agencies
- ≥90% precision on ticker mapping
- Confidence scoring for all mappings

### ✅ Playbook Cards
- Entry triggers (price level, drawdown, MA cross, time stop, event)
- Exit invalidators (time stop, price level, events)
- Catalysts and risks with provenance
- Explainability (quote references)

### ✅ Discovery Engine
- Similar-logic ticker recommendations
- Multilingual embeddings (mE5)
- Feature-based matching (themes, catalysts, geography)
- Full explainability for every recommendation

### ✅ Paper Portfolio
- One-click position entry from alerts
- Real-time P&L tracking
- Win rate, max drawdown, TWR
- Position history

### ✅ Trigger Engine
- EOD evaluation (runs at 22:00 daily)
- Email/Slack/Telegram alerts
- Auto-enter paper positions (optional)

## Troubleshooting

### Database Connection Error

```
Error: connection refused
```

**Solution:** Make sure PostgreSQL is running and the `DATABASE_URL` is correct.

```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT version();"

# Verify database exists
psql -U postgres -l | grep thesis_ticker_engine
```

### Missing pgvector Extension

```
Error: type "vector" does not exist
```

**Solution:** Install and enable pgvector:

```bash
# Install pgvector
# On macOS: brew install pgvector
# On Ubuntu: apt-get install postgresql-15-pgvector

# Enable in database
psql thesis_ticker_engine -c "CREATE EXTENSION vector;"
```

### NLP Model Download Issues

The first run might be slow as it downloads models. To pre-download:

```python
from sentence_transformers import SentenceTransformer

# Download multilingual embedding model
model = SentenceTransformer('intfloat/multilingual-e5-base')
```

### Frontend Build Error

```
Error: Module not found
```

**Solution:** Clean install dependencies:

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Production Deployment

### 1. Build Docker Images

```bash
docker-compose build
```

### 2. Configure Production Environment

Update `.env` with production values:
- Set `API_DEBUG=False`
- Use strong `SECRET_KEY`
- Configure real SMTP/webhook credentials
- Use managed PostgreSQL (RDS, Cloud SQL, etc.)

### 3. Deploy

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Set Up Monitoring

- Add health check endpoints
- Monitor `/healthz` endpoint
- Set up log aggregation
- Configure alerting for worker failures

## License

MIT
