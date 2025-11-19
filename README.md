# Thesis → Ticker Engine

Turn weekly macro/investing lessons into **clear trade plans on real tickers**, with **explainable triggers**, **invalidators**, and a **discovery engine** that finds **similar-logic opportunities**—all tracked with paper PnL.

## Features

- ✅ Bilingual (CN/EN) ingest and extraction
- ✅ NER and entity extraction for companies, commodities, instruments
- ✅ Ticker mapping with confidence scoring
- ✅ Playbook card generation with entry/exit/invalidators
- ✅ Trigger engine (price levels, drawdowns, MA crosses, time stops)
- ✅ Alert system (email/webhook)
- ✅ Paper portfolio with PnL tracking
- ✅ Similar-logic discovery engine
- ✅ Full explainability and provenance tracking

## Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL 15+ with pgvector
- **NLP**: XLM-R, mE5 embeddings, Jieba (Chinese)
- **Deployment**: Docker, Docker Compose

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL 15+ with pgvector extension
- Docker & Docker Compose (optional)

### Setup

1. **Database**:
```bash
cd backend
python scripts/init_db.py
```

2. **Backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

3. **Frontend**:
```bash
cd frontend
npm install
npm run dev
```

4. **Access**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── api/                 # API routes
│   │   ├── models/              # SQLAlchemy models
│   │   ├── services/            # Business logic
│   │   │   ├── ingest.py        # Transcript extraction
│   │   │   ├── ner.py           # Named entity recognition
│   │   │   ├── ticker_mapper.py # Ticker mapping
│   │   │   ├── card_generator.py# Card generation
│   │   │   ├── triggers.py      # Trigger evaluation
│   │   │   ├── discovery.py     # Similar-logic engine
│   │   │   └── translation.py   # MT with glossary
│   │   ├── db/                  # Database utilities
│   │   └── workers/             # Cron workers
│   ├── tests/                   # Backend tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/                     # Next.js app router
│   │   ├── [locale]/            # i18n routing
│   │   │   ├── ingest/          # Ingest page
│   │   │   ├── playbook/        # Playbook page
│   │   │   ├── alerts/          # Alerts page
│   │   │   └── scoreboard/      # Scoreboard page
│   ├── components/              # React components
│   ├── lib/                     # Utilities
│   ├── public/                  # Static assets
│   ├── next.config.js           # Next.js config with i18n
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Development

### Running Tests

**Backend**:
```bash
cd backend
pytest tests/ -v --cov=app
```

**Frontend**:
```bash
cd frontend
npm test
```

### Database Migrations

```bash
cd backend
alembic upgrade head
```

### Seed Data

```bash
cd backend
python scripts/seed_glossary.py
python scripts/seed_instruments.py
```

## API Documentation

Full API documentation available at http://localhost:8000/docs

Key endpoints:
- `POST /ingest` - Ingest transcript and generate draft cards
- `GET /cards` - List playbook cards
- `PUT /cards/{id}` - Update card
- `POST /alerts/enable` - Enable alerts for a card
- `GET /portfolio` - Get paper portfolio
- `GET /cards/{id}/similar` - Get similar tickers

## License

MIT
