# Complete Deployment & Testing Guide

This guide provides **exact commands** to deploy and test the Thesis → Ticker Engine both locally and in production.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Testing the Application](#testing-the-application)
4. [Production Deployment](#production-deployment)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

**Option 1: Docker (Recommended - Easiest)**
```bash
# Install Docker Desktop (includes Docker Compose)
# macOS: https://docs.docker.com/desktop/install/mac-install/
# Windows: https://docs.docker.com/desktop/install/windows-install/
# Linux: https://docs.docker.com/desktop/install/linux-install/

# Verify installation
docker --version
docker-compose --version
```

**Option 2: Manual Install**
```bash
# Python 3.11+
python3 --version  # Should be 3.11 or higher

# Node.js 18+
node --version  # Should be 18.x or higher
npm --version

# PostgreSQL 15+ with pgvector
psql --version  # Should be 15.x or higher
```

---

## Local Development Setup

### Option A: Docker (Recommended - One Command!)

```bash
# Step 1: Clone the repository
git clone https://github.com/RileyLin/trend-analysis.git
cd trend-analysis

# Step 2: Create environment file
cp .env.example .env

# Step 3: Start everything
docker-compose up -d

# Step 4: Wait for services to be ready (30-60 seconds)
# Check status
docker-compose ps

# You should see:
# thesis-ticker-db        running (healthy)
# thesis-ticker-backend   running
# thesis-ticker-frontend  running

# Step 5: Initialize database
docker-compose exec backend python scripts/init_db.py

# Expected output:
# Initializing database...
# ✓ pgvector extension created/verified
# Database tables created successfully!

# Step 6: Seed initial data
docker-compose exec backend python scripts/seed_glossary.py
# Expected output: ✓ Seeded 24 glossary terms

docker-compose exec backend python scripts/seed_instruments.py
# Expected output: ✓ Seeded 7 instruments

# Step 7: Access the application
echo "✅ Application is ready!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
```

**To stop:**
```bash
docker-compose down
```

**To restart:**
```bash
docker-compose up -d
```

**To view logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

### Option B: Manual Setup (No Docker)

#### Step 1: Setup PostgreSQL

```bash
# macOS (Homebrew)
brew install postgresql@15 pgvector
brew services start postgresql@15

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql-15 postgresql-15-pgvector
sudo systemctl start postgresql

# Create database
createdb thesis_ticker_engine

# Enable pgvector extension
psql thesis_ticker_engine -c "CREATE EXTENSION vector;"

# Verify
psql thesis_ticker_engine -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

#### Step 2: Setup Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# This will install 48 packages including:
# - FastAPI, SQLAlchemy, PostgreSQL drivers
# - NLP libraries (transformers, spaCy, Jieba)
# - ML libraries (torch, sentence-transformers)
# - Data libraries (pandas, numpy)
# Total install time: 5-10 minutes

# Set database URL
export DATABASE_URL="postgresql://postgres:password@localhost:5432/thesis_ticker_engine"

# Initialize database
python scripts/init_db.py

# Seed data
python scripts/seed_glossary.py
python scripts/seed_instruments.py

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Backend is now running at http://localhost:8000
# Keep this terminal open!
```

#### Step 3: Setup Frontend (New Terminal)

```bash
cd frontend

# Install dependencies
npm install

# This will install 20 packages including:
# - Next.js 14, React 18, TypeScript
# - Tailwind CSS, axios, date-fns
# Total install time: 1-2 minutes

# Set API URL (optional - defaults to localhost:8000)
export NEXT_PUBLIC_API_URL="http://localhost:8000/api"

# Start frontend server
npm run dev

# Frontend is now running at http://localhost:3000
# Keep this terminal open!
```

#### Step 4: Access the Application

Open your browser:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## Testing the Application

### 1. Quick Health Check

```bash
# Test backend health
curl http://localhost:8000/healthz

# Expected response:
# {"status":"healthy","service":"thesis-ticker-engine"}

# Test database connection
docker-compose exec backend python -c "from app.db.database import engine; print(engine.connect())"

# Expected: Connection object (no errors)
```

### 2. Run Automated Tests

#### Backend Tests

```bash
cd backend

# Run all tests
pytest tests/ -v

# Expected output:
# tests/test_language_utils.py::TestLanguageDetector::test_detect_chinese PASSED
# tests/test_language_utils.py::TestLanguageDetector::test_detect_english PASSED
# tests/test_ner.py::TestNERService::test_extract_companies PASSED
# tests/test_api.py::TestIngestAPI::test_ingest_simple_text PASSED
# ...
# ========== X passed in Y.YYs ==========

# With coverage report
pytest tests/ -v --cov=app --cov-report=html

# Open coverage report
# macOS: open htmlcov/index.html
# Linux: xdg-open htmlcov/index.html
# Windows: start htmlcov/index.html
```

#### End-to-End Test

```bash
cd backend

# Make sure backend and frontend are running!
python scripts/test_e2e.py

# Expected output:
# ============================================================
# End-to-End Testing - Thesis → Ticker Engine
# ============================================================
# ✓ API is healthy
#
# === Testing Ingest ===
# ✓ Processing time: 2.43s
# ✓ Entities extracted: 15
# ✓ Cards generated: 3
#
#   Card: card_20250119_001
#     Summary (EN): Watch IONQ based on relevant catalysts
#     Summary (CN): 关注 IONQ，基于相关催化剂和市场机会
#     Instruments: ['IONQ']
#     Confidence: 0.75
#
# === Testing Cards API ===
# ✓ Total cards in system: 3
# ✓ Retrieved card card_20250119_001
#
# === Testing Alerts ===
# ✓ Alerts enabled for card card_20250119_001
# ✓ Total alerts: 0
#
# === Testing Discovery Engine ===
# ✓ Similar tickers found: 5
#   MP: 0.82
#     Matched on theme=rare_earths, catalyst=export_controls, geo=US
#   LYC: 0.75
#     Matched on theme=rare_earths, catalyst=supply_chain, geo=AU
#
# === Testing Portfolio ===
# ✓ Position opened
# ✓ Total positions: 1
# ✓ Portfolio stats:
#   Total positions: 1
#   Total P&L: $0.00
#   Win rate: 0.0%
#
# ============================================================
# ✅ All E2E tests passed!
# ============================================================
```

### 3. Manual UI Testing

#### Test 1: Ingest Transcript

```bash
# 1. Navigate to http://localhost:3000/en-US/ingest

# 2. Paste this sample transcript:
```

**Sample Transcript (copy this):**
```
量子计算投资机会分析

IonQ是一家领先的量子计算公司，在NASDAQ上市。美国政府计划投资量子技术，每家公司可能获得约1000万美元的资助。

This represents a significant catalyst for quantum computing companies. IonQ has demonstrated strong technical capabilities with their ion-trap technology.

Entry strategy: Consider buying IonQ on pullbacks to $12-13 levels. The stock has shown support at these levels historically.

Invalidation: If government funding is delayed beyond Q2 2025, or if the stock falls below $10, exit the position.

稀土供应链分析

MP Materials (MP) is the only rare earth mining company in North America. With potential export controls from China, MP could benefit significantly.

中国可能限制稀土出口，这将使得北美稀土生产商受益。MP Materials 位于加利福尼亚，是美国唯一的稀土矿商。

Target entry: MP at $18-20 range on any market weakness.

Risk: Permitting delays or environmental concerns could impact production.
```

```bash
# 3. Click "Extract Cards"
# 4. Wait 2-5 seconds
# 5. Verify you see draft cards on the right:
#    - At least 1-2 cards generated
#    - Each card has: ticker symbol, direction, triggers, invalidators
#    - Both CN and EN summaries present
# 6. Click "Save" on a card
# 7. Check browser console for errors (should be none)
```

#### Test 2: View Playbook

```bash
# 1. Navigate to http://localhost:3000/en-US/playbook
# 2. Verify you see the saved cards
# 3. Click "Similar Tickers" on a card
# 4. Verify similar tickers appear (may take 1-2 seconds)
# 5. Click "Enable Alerts" on a card
# 6. Verify success message appears
```

#### Test 3: Bilingual Support

```bash
# 1. On any page, click the language toggle (EN/中文)
# 2. Verify page switches to Chinese
# 3. Navigate to /zh-CN/playbook
# 4. Verify all UI text is in Chinese
# 5. Verify card content shows CN summaries
# 6. Switch back to English
```

#### Test 4: Scoreboard

```bash
# 1. Navigate to http://localhost:3000/en-US/scoreboard
# 2. Verify portfolio stats display (may be $0 if no positions)
# 3. Verify table shows columns: Symbol, Entry, Current/Exit, P&L, etc.
```

### 4. API Testing (via Swagger UI)

```bash
# 1. Open http://localhost:8000/docs
# 2. Try these endpoints:

# Test /healthz
GET /healthz
# Click "Try it out" → "Execute"
# Response should be: {"status":"healthy",...}

# Test /api/cards
GET /api/cards
# Click "Try it out" → "Execute"
# Response should be array of cards

# Test /api/ingest
POST /api/ingest
# Click "Try it out"
# Paste in Request body:
{
  "text": "IonQ is a quantum computing company trading on NASDAQ at $12.",
  "locale": "en-US"
}
# Click "Execute"
# Response should have "cards" array with at least 1 card
```

---

## Production Deployment

### Option 1: VPS Deployment (DigitalOcean, Linode, AWS EC2)

#### Step 1: Provision VPS

```bash
# Recommended specs:
# - 2 vCPUs
# - 4GB RAM
# - 50GB SSD
# - Ubuntu 22.04 LTS

# SSH into your server
ssh root@your-server-ip
```

#### Step 2: Install Docker

```bash
# Update system
apt-get update
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt-get install -y docker-compose-plugin

# Verify
docker --version
docker compose version
```

#### Step 3: Setup Application

```bash
# Create directory
mkdir -p /opt/thesis-ticker-engine
cd /opt/thesis-ticker-engine

# Clone repository
git clone https://github.com/RileyLin/trend-analysis.git .

# Checkout the correct branch
git checkout claude/thesis-ticker-engine-01JxqBhQpjYwf7rWBZHgcnuR

# Create production environment file
cp .env.example .env.production

# Edit environment variables
nano .env.production

# Update these values:
# DATABASE_URL=postgresql://user:password@postgres-host:5432/thesis_ticker_engine
# API_DEBUG=False
# SECRET_KEY=<generate random key>
# SMTP_HOST=smtp.gmail.com
# SMTP_USER=your-email@gmail.com
# SMTP_PASSWORD=your-app-password
# NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api

# Generate secret key:
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

#### Step 4: Setup Database

**Option A: Use managed PostgreSQL (Recommended)**
```bash
# Use DigitalOcean Managed Databases, AWS RDS, or similar
# Get connection string from provider
# Update DATABASE_URL in .env.production
```

**Option B: Self-hosted PostgreSQL**
```bash
# Install PostgreSQL
apt-get install -y postgresql-15 postgresql-contrib-15

# Install pgvector
apt-get install -y postgresql-15-pgvector

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE thesis_ticker_engine;
CREATE USER appuser WITH ENCRYPTED PASSWORD 'strong-password-here';
GRANT ALL PRIVILEGES ON DATABASE thesis_ticker_engine TO appuser;
\c thesis_ticker_engine
CREATE EXTENSION vector;
EOF

# Update DATABASE_URL in .env.production:
# DATABASE_URL=postgresql://appuser:strong-password-here@localhost:5432/thesis_ticker_engine
```

#### Step 5: Deploy with Docker

```bash
# Build images
docker compose -f docker-compose.yml build

# Start services
docker compose up -d

# Initialize database
docker compose exec backend python scripts/init_db.py
docker compose exec backend python scripts/seed_glossary.py
docker compose exec backend python scripts/seed_instruments.py

# Check status
docker compose ps

# View logs
docker compose logs -f
```

#### Step 6: Setup Nginx + SSL

```bash
# Install Nginx
apt-get install -y nginx certbot python3-certbot-nginx

# Create Nginx config
cat > /etc/nginx/sites-available/thesis-ticker << 'EOF'
# Backend API
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Frontend
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/thesis-ticker /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx

# Get SSL certificates
certbot --nginx -d api.yourdomain.com -d yourdomain.com -d www.yourdomain.com --non-interactive --agree-tos -m your-email@gmail.com

# Verify auto-renewal
certbot renew --dry-run
```

#### Step 7: Verify Production Deployment

```bash
# Test health
curl https://api.yourdomain.com/healthz

# Test frontend
curl -I https://yourdomain.com

# Run E2E test against production
cd /opt/thesis-ticker-engine/backend
PROD_API_URL=https://api.yourdomain.com/api python scripts/test_e2e.py
```

---

### Option 2: Quick Deploy to Vercel (Frontend) + Railway (Backend)

#### Frontend to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel --prod

# Follow prompts:
# - Link to existing project or create new
# - Set environment variable: NEXT_PUBLIC_API_URL=https://your-backend-url/api

# Your frontend is now live at: https://your-project.vercel.app
```

#### Backend + Database to Railway

```bash
# 1. Go to https://railway.app
# 2. Click "New Project"
# 3. Select "Deploy from GitHub repo"
# 4. Connect your repository
# 5. Railway will auto-detect Dockerfile and deploy
# 6. Add PostgreSQL plugin (Railway provides pgvector)
# 7. Set environment variables in Railway dashboard
# 8. Run initialization commands in Railway terminal:
#    python scripts/init_db.py
#    python scripts/seed_glossary.py
#    python scripts/seed_instruments.py
```

---

## Troubleshooting

### Problem: Docker containers won't start

```bash
# Check Docker is running
docker ps

# Check logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db

# Common fixes:
# 1. Port already in use
sudo lsof -i :8000  # Check what's using port 8000
sudo lsof -i :3000  # Check what's using port 3000
sudo lsof -i :5432  # Check what's using port 5432

# 2. Rebuild images
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Problem: Database connection error

```bash
# Test PostgreSQL connection
docker-compose exec db psql -U postgres -c "SELECT 1"

# Check DATABASE_URL
docker-compose exec backend env | grep DATABASE_URL

# Verify pgvector extension
docker-compose exec db psql -U postgres -d thesis_ticker_engine -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# If extension missing:
docker-compose exec db psql -U postgres -d thesis_ticker_engine -c "CREATE EXTENSION vector;"
```

### Problem: Frontend shows API errors

```bash
# Check backend is accessible
curl http://localhost:8000/healthz

# Check CORS settings in backend
# File: backend/app/main.py
# Ensure CORS middleware allows your frontend origin

# Check API URL in frontend
# Should be: http://localhost:8000/api (development)
# or: https://api.yourdomain.com/api (production)
```

### Problem: Slow ingest processing

```bash
# First run downloads NLP models (one-time, 5-10 minutes)
# Subsequent runs should be fast (2-5 seconds for 10k words)

# Check logs for model download progress
docker-compose logs -f backend | grep -i "download\|model"

# Models are cached in Docker volume, persist across restarts
```

### Problem: No similar tickers found

```bash
# Make sure you've seeded instruments
docker-compose exec backend python scripts/seed_instruments.py

# Check instrument count
docker-compose exec backend python -c "from app.db.database import SessionLocal; from app.models.instrument import Instrument; db = SessionLocal(); print(f'Instruments: {db.query(Instrument).count()}'); db.close()"

# Should show: Instruments: 7 (or more)
```

### Problem: Tests failing

```bash
# Backend tests
cd backend

# Install test dependencies
pip install pytest pytest-cov

# Run with verbose output
pytest tests/ -v -s

# Run specific test
pytest tests/test_api.py::TestIngestAPI::test_ingest_simple_text -v -s
```

---

## Next Steps

1. **Customize Data:**
   - Add more instruments: Edit `backend/scripts/seed_instruments.py`
   - Add more glossary terms: Edit `backend/scripts/seed_glossary.py`

2. **Configure Alerts:**
   - Set up SMTP in `.env` for email alerts
   - Add Slack webhook for Slack notifications

3. **Enable Worker:**
   - Uncomment worker service in `docker-compose.yml`
   - Configure EOD_UPDATE_HOUR for trigger evaluation

4. **Monitor:**
   - Check logs: `docker-compose logs -f`
   - Monitor resources: `docker stats`
   - Set up health checks and uptime monitoring

5. **Scale:**
   - See DEPLOYMENT.md for scaling strategies
   - Consider managed services for production

---

## Quick Reference

### Development Commands

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# View logs
docker-compose logs -f [service]

# Run tests
cd backend && pytest tests/

# Run E2E test
cd backend && python scripts/test_e2e.py

# Database shell
docker-compose exec db psql -U postgres -d thesis_ticker_engine

# Backend shell
docker-compose exec backend python

# Reset database
docker-compose exec backend python scripts/init_db.py
docker-compose exec backend python scripts/seed_glossary.py
docker-compose exec backend python scripts/seed_instruments.py
```

### Service URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **API Redoc:** http://localhost:8000/redoc

---

**🎉 You're all set! The application is fully functional and ready for use.**
