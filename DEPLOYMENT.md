# Deployment Guide - Thesis → Ticker Engine

This guide covers deploying the Thesis → Ticker Engine to production environments.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [Worker Deployment](#worker-deployment)
7. [Infrastructure Options](#infrastructure-options)
8. [Monitoring & Logging](#monitoring--logging)
9. [Backup & Recovery](#backup--recovery)
10. [Scaling Considerations](#scaling-considerations)
11. [Security Hardening](#security-hardening)
12. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

Before deploying to production, ensure you have:

- [ ] PostgreSQL 15+ instance with pgvector extension
- [ ] Domain name(s) configured with DNS
- [ ] SSL/TLS certificates (Let's Encrypt recommended)
- [ ] SMTP credentials for email alerts (Gmail, SendGrid, etc.)
- [ ] Webhook URLs configured (Slack/Telegram)
- [ ] Environment variables secured
- [ ] Backup strategy defined
- [ ] Monitoring solution chosen
- [ ] CI/CD pipeline configured (optional)

---

## Environment Setup

### 1. Production Environment Variables

Create a `.env.production` file:

```bash
# Database (use managed PostgreSQL)
DATABASE_URL=postgresql://username:password@postgres-host:5432/thesis_ticker_engine

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=False
SECRET_KEY=<generate-strong-random-key-here>

# CORS Origins (your frontend domain)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# NLP Models (will be cached after first download)
NER_MODEL=xlm-roberta-base
EMBEDDING_MODEL=intfloat/multilingual-e5-base

# Email Configuration (for alerts)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-production-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_USE_TLS=True
ALERT_FROM_EMAIL=alerts@yourdomain.com

# Webhook Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-telegram-chat-id

# Data Sources
PRICE_DATA_SOURCE=yfinance
EOD_UPDATE_HOUR=22
EOD_UPDATE_TIMEZONE=America/New_York

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Frontend
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api
```

### 2. Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

## Database Setup

### Option 1: Managed PostgreSQL (Recommended)

#### AWS RDS

```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier thesis-ticker-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 15.3 \
  --master-username admin \
  --master-user-password <strong-password> \
  --allocated-storage 50 \
  --storage-type gp3 \
  --vpc-security-group-ids sg-xxxxx \
  --db-subnet-group-name my-db-subnet-group \
  --backup-retention-period 7 \
  --multi-az

# Wait for instance to be available
aws rds wait db-instance-available --db-instance-identifier thesis-ticker-db

# Get endpoint
aws rds describe-db-instances \
  --db-instance-identifier thesis-ticker-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text
```

#### Google Cloud SQL

```bash
# Create Cloud SQL instance
gcloud sql instances create thesis-ticker-db \
  --database-version=POSTGRES_15 \
  --tier=db-custom-2-8192 \
  --region=us-central1 \
  --backup \
  --backup-start-time=03:00

# Create database
gcloud sql databases create thesis_ticker_engine \
  --instance=thesis-ticker-db

# Create user
gcloud sql users create appuser \
  --instance=thesis-ticker-db \
  --password=<strong-password>
```

#### DigitalOcean Managed Databases

```bash
# Via DigitalOcean console or doctl CLI
doctl databases create thesis-ticker-db \
  --engine pg \
  --version 15 \
  --size db-s-2vcpu-4gb \
  --region nyc1
```

### Option 2: Self-Hosted PostgreSQL

If self-hosting, ensure:

1. **PostgreSQL 15+ installed**
2. **pgvector extension enabled**
3. **Regular backups configured**
4. **Secure networking (firewall, VPC)**
5. **SSL/TLS enabled**

```bash
# Install PostgreSQL 15
sudo apt-get update
sudo apt-get install -y postgresql-15 postgresql-contrib-15

# Install pgvector
sudo apt-get install -y postgresql-15-pgvector

# Configure PostgreSQL
sudo -u postgres psql << EOF
CREATE DATABASE thesis_ticker_engine;
CREATE USER appuser WITH ENCRYPTED PASSWORD 'strong-password';
GRANT ALL PRIVILEGES ON DATABASE thesis_ticker_engine TO appuser;
\c thesis_ticker_engine
CREATE EXTENSION vector;
EOF
```

### Enable pgvector Extension

```sql
-- Connect to your database
\c thesis_ticker_engine

-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### Initialize Database Schema

```bash
# Set DATABASE_URL
export DATABASE_URL="postgresql://username:password@host:5432/thesis_ticker_engine"

# Run initialization
cd backend
python scripts/init_db.py

# Seed initial data
python scripts/seed_glossary.py
python scripts/seed_instruments.py
```

---

## Backend Deployment

### Option 1: Docker on VPS (DigitalOcean, Linode, etc.)

#### Setup VPS

```bash
# SSH into your VPS
ssh root@your-server-ip

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
apt-get install -y docker-compose-plugin

# Create application directory
mkdir -p /opt/thesis-ticker-engine
cd /opt/thesis-ticker-engine
```

#### Deploy Application

```bash
# Clone repository (or copy files)
git clone <your-repo-url> .
git checkout main

# Copy production environment
cp .env.example .env.production
nano .env.production  # Edit with production values

# Create docker-compose.production.yml
cat > docker-compose.production.yml << 'EOF'
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: thesis-ticker-backend
    env_file:
      - .env.production
    ports:
      - "8000:8000"
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - app-network

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: thesis-ticker-worker
    env_file:
      - .env.production
    command: python app/workers/eod_trigger_worker.py
    restart: unless-stopped
    depends_on:
      - backend
    networks:
      - app-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: thesis-ticker-frontend
    environment:
      - NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api
    ports:
      - "3000:3000"
    restart: unless-stopped
    depends_on:
      - backend
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
EOF

# Build and start
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d

# View logs
docker-compose -f docker-compose.production.yml logs -f
```

#### Setup Nginx Reverse Proxy

```bash
# Install Nginx
apt-get install -y nginx certbot python3-certbot-nginx

# Configure Nginx
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

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
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

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/thesis-ticker /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx

# Get SSL certificates
certbot --nginx -d api.yourdomain.com -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is configured automatically by certbot
```

### Option 2: AWS ECS/Fargate

#### Create ECR Repositories

```bash
# Create repositories
aws ecr create-repository --repository-name thesis-ticker-backend
aws ecr create-repository --repository-name thesis-ticker-frontend
aws ecr create-repository --repository-name thesis-ticker-worker

# Get login credentials
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

#### Build and Push Images

```bash
# Backend
cd backend
docker build -t thesis-ticker-backend:latest .
docker tag thesis-ticker-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/thesis-ticker-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/thesis-ticker-backend:latest

# Frontend
cd ../frontend
docker build -t thesis-ticker-frontend:latest .
docker tag thesis-ticker-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/thesis-ticker-frontend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/thesis-ticker-frontend:latest

# Worker
docker tag thesis-ticker-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/thesis-ticker-worker:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/thesis-ticker-worker:latest
```

#### Create ECS Task Definitions

See `deployment/ecs-task-definition.json` (create this file with your specific configuration)

#### Deploy Services

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name thesis-ticker-cluster

# Register task definitions and create services
# (Use AWS Console or CLI with task definition files)
```

### Option 3: Google Cloud Run

```bash
# Backend
cd backend
gcloud builds submit --tag gcr.io/PROJECT-ID/thesis-ticker-backend
gcloud run deploy thesis-ticker-backend \
  --image gcr.io/PROJECT-ID/thesis-ticker-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=$DATABASE_URL

# Frontend
cd ../frontend
gcloud builds submit --tag gcr.io/PROJECT-ID/thesis-ticker-frontend
gcloud run deploy thesis-ticker-frontend \
  --image gcr.io/PROJECT-ID/thesis-ticker-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars NEXT_PUBLIC_API_URL=https://thesis-ticker-backend-xxx.run.app/api

# Worker (Cloud Run Jobs)
gcloud builds submit --tag gcr.io/PROJECT-ID/thesis-ticker-worker
gcloud run jobs create thesis-ticker-worker \
  --image gcr.io/PROJECT-ID/thesis-ticker-worker \
  --region us-central1 \
  --set-env-vars DATABASE_URL=$DATABASE_URL \
  --schedule "0 22 * * *"  # Daily at 22:00
```

### Option 4: Kubernetes (Advanced)

See `deployment/kubernetes/` directory for manifests.

---

## Frontend Deployment

### Option 1: Vercel (Recommended for Next.js)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel --prod

# Set environment variables in Vercel dashboard
# NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api
```

### Option 2: Netlify

```bash
# netlify.toml
[build]
  command = "npm run build"
  publish = ".next"

[build.environment]
  NEXT_PUBLIC_API_URL = "https://api.yourdomain.com/api"
```

### Option 3: Self-Hosted (with Docker)

Already covered in Backend Deployment Option 1.

---

## Worker Deployment

The EOD trigger worker must run daily to evaluate triggers and generate alerts.

### Option 1: Systemd Service (VPS)

```bash
# Create systemd service
cat > /etc/systemd/system/thesis-ticker-worker.service << 'EOF'
[Unit]
Description=Thesis Ticker Engine - EOD Worker
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/thesis-ticker-engine/backend
Environment="DATABASE_URL=postgresql://..."
ExecStart=/opt/thesis-ticker-engine/backend/venv/bin/python app/workers/eod_trigger_worker.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
systemctl daemon-reload
systemctl enable thesis-ticker-worker
systemctl start thesis-ticker-worker
systemctl status thesis-ticker-worker
```

### Option 2: Cron Job

```bash
# Add to crontab
crontab -e

# Run daily at 22:00
0 22 * * * cd /opt/thesis-ticker-engine/backend && /opt/thesis-ticker-engine/backend/venv/bin/python -c "from app.workers.eod_trigger_worker import run_eod_trigger_evaluation; run_eod_trigger_evaluation()" >> /var/log/thesis-ticker-worker.log 2>&1
```

### Option 3: Cloud Scheduler + Cloud Functions

```python
# cloud_function/main.py
from app.workers.eod_trigger_worker import run_eod_trigger_evaluation

def trigger_evaluation(request):
    run_eod_trigger_evaluation()
    return 'OK'
```

Deploy and set up Cloud Scheduler to call the function daily.

---

## Monitoring & Logging

### Application Monitoring

#### Option 1: Sentry (Errors)

```python
# backend/app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment="production"
)
```

#### Option 2: Prometheus + Grafana (Metrics)

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3001:3000"
    depends_on:
      - prometheus

volumes:
  prometheus_data:
  grafana_data:
```

### Logging

#### Centralized Logging with ELK Stack

```bash
# docker-compose.logging.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

#### Cloud-Native Logging

**AWS CloudWatch:**
```bash
# Configure Docker to send logs to CloudWatch
# In docker-compose.production.yml
services:
  backend:
    logging:
      driver: awslogs
      options:
        awslogs-group: /ecs/thesis-ticker-backend
        awslogs-region: us-east-1
        awslogs-stream-prefix: ecs
```

**Google Cloud Logging:**
Automatically configured when using Cloud Run.

---

## Backup & Recovery

### Database Backups

#### Automated Daily Backups

```bash
# Create backup script
cat > /opt/thesis-ticker-engine/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="thesis_ticker_engine"
DB_USER="appuser"
DB_HOST="localhost"

mkdir -p $BACKUP_DIR

# Create backup
PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -U $DB_USER $DB_NAME | \
  gzip > $BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

# Upload to S3 (optional)
# aws s3 cp $BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz s3://your-backup-bucket/
EOF

chmod +x /opt/thesis-ticker-engine/backup.sh

# Add to crontab
crontab -e
# Daily at 3 AM
0 3 * * * /opt/thesis-ticker-engine/backup.sh >> /var/log/backup.log 2>&1
```

#### Managed Database Backups

Most managed database services (RDS, Cloud SQL) have automatic backup configuration.

**AWS RDS:**
- Automated backups (retention: 7-35 days)
- Manual snapshots (retained indefinitely)

**Google Cloud SQL:**
- Automated backups (retention: 7-365 days)
- On-demand backups

### Restore from Backup

```bash
# Decompress and restore
gunzip < /backups/postgres/thesis_ticker_engine_20250119_030000.sql.gz | \
  psql -h localhost -U appuser thesis_ticker_engine
```

---

## Scaling Considerations

### Horizontal Scaling

#### Backend API

```bash
# With Docker Compose
docker-compose -f docker-compose.production.yml up -d --scale backend=3

# Add load balancer (Nginx)
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

#### Database Read Replicas

For read-heavy workloads, configure PostgreSQL read replicas:

```python
# backend/app/db/database.py
# Primary (write)
write_engine = create_engine(WRITE_DB_URL)

# Replica (read)
read_engine = create_engine(READ_DB_URL)

def get_read_db():
    """For read-only operations."""
    db = SessionMaker(bind=read_engine)()
    try:
        yield db
    finally:
        db.close()
```

### Vertical Scaling

Increase resources based on monitoring:

- **CPU-bound:** Increase vCPUs for NER/embedding operations
- **Memory-bound:** Increase RAM for model caching
- **I/O-bound:** Use SSDs, increase IOPS for database

### Caching

```python
# Add Redis for caching
# backend/app/services/cache.py
import redis
from functools import wraps

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=6379,
    decode_responses=True
)

def cache_result(ttl=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

---

## Security Hardening

### 1. Environment Variables

- **Never commit `.env` files**
- Use secrets management (AWS Secrets Manager, Vault)
- Rotate credentials regularly

### 2. HTTPS Only

```nginx
# Force HTTPS redirect
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### 3. Rate Limiting

```python
# backend/app/main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/ingest")
@limiter.limit("10/hour")
async def ingest_transcript(...):
    ...
```

### 4. Input Validation

All inputs are validated via Pydantic schemas (already implemented).

### 5. SQL Injection Prevention

Using SQLAlchemy ORM (parameterized queries) - already safe.

### 6. CORS Configuration

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://www.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 7. Database Security

- Use strong passwords (20+ characters)
- Enable SSL/TLS for database connections
- Restrict network access (VPC, security groups)
- Regular security updates

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Timeouts

```python
# Increase pool size
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True  # Verify connections before use
)
```

#### 2. Memory Issues with NLP Models

```python
# Lazy load models
from functools import lru_cache

@lru_cache(maxsize=1)
def get_embedding_model():
    return SentenceTransformer('intfloat/multilingual-e5-base')
```

#### 3. Worker Not Running

```bash
# Check logs
docker-compose logs worker

# Verify cron schedule
docker-compose exec worker crontab -l
```

#### 4. Slow Ingest Performance

- Increase worker processes
- Use async processing
- Cache NER patterns
- Optimize database queries

### Health Checks

```bash
# Backend health
curl https://api.yourdomain.com/healthz

# Database connectivity
psql $DATABASE_URL -c "SELECT 1"

# Worker status
systemctl status thesis-ticker-worker
```

---

## Post-Deployment

### 1. Verify Deployment

```bash
# Run E2E test against production
PROD_API_URL=https://api.yourdomain.com/api python backend/scripts/test_e2e.py
```

### 2. Monitor Initial Traffic

- Watch error rates in Sentry
- Check response times
- Monitor database connections

### 3. Set Up Alerts

Configure alerts for:
- API errors (>1% error rate)
- Database connection failures
- Worker execution failures
- High memory usage (>80%)
- Disk space (>80% full)

### 4. Documentation

Update internal documentation with:
- Production URLs
- Deployment procedures
- Rollback procedures
- On-call contact information

---

## Rollback Procedure

If deployment fails:

```bash
# Docker-based deployment
docker-compose -f docker-compose.production.yml down
git checkout <previous-stable-commit>
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d

# Kubernetes
kubectl rollout undo deployment/thesis-ticker-backend

# Restore database backup if needed
gunzip < backup.sql.gz | psql $DATABASE_URL
```

---

## Support & Maintenance

### Regular Maintenance Tasks

**Weekly:**
- Review error logs
- Check backup success
- Monitor disk usage

**Monthly:**
- Update dependencies
- Review and optimize slow queries
- Analyze usage patterns
- Update SSL certificates (if manual)

**Quarterly:**
- Security audit
- Performance optimization
- Database vacuum and reindex
- Disaster recovery drill

---

## Contact & Support

For deployment issues or questions:
- GitHub Issues: [your-repo]/issues
- Email: support@yourdomain.com
- Documentation: https://docs.yourdomain.com

---

**Last Updated:** 2025-01-19
**Version:** 1.0.0
