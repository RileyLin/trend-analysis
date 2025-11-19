.PHONY: help install dev build test clean

help:
	@echo "Thesis → Ticker Engine - Development Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make install     - Install all dependencies"
	@echo "  make dev         - Start development environment"
	@echo "  make build       - Build Docker containers"
	@echo "  make test        - Run tests"
	@echo "  make clean       - Clean up"
	@echo "  make init-db     - Initialize database"
	@echo "  make seed        - Seed database with initial data"

install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Done!"

dev:
	@echo "Starting development environment with Docker Compose..."
	docker-compose up

build:
	@echo "Building Docker containers..."
	docker-compose build

test:
	@echo "Running backend tests..."
	cd backend && pytest tests/ -v
	@echo "Running frontend tests..."
	cd frontend && npm test

clean:
	@echo "Cleaning up..."
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	@echo "Done!"

init-db:
	@echo "Initializing database..."
	cd backend && python scripts/init_db.py

seed:
	@echo "Seeding database..."
	cd backend && python scripts/seed_glossary.py
	cd backend && python scripts/seed_instruments.py
	@echo "Done!"

# Quick start for development (without Docker)
dev-local:
	@echo "Starting local development..."
	@echo "Make sure PostgreSQL is running on localhost:5432"
	@echo ""
	@echo "Terminal 1: Backend"
	@echo "  cd backend && uvicorn app.main:app --reload"
	@echo ""
	@echo "Terminal 2: Frontend"
	@echo "  cd frontend && npm run dev"
