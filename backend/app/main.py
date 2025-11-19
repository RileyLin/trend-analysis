"""FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from app.api import ingest, cards, alerts, portfolio, similarity
from app.db.database import init_db

load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Thesis → Ticker Engine API",
    description="Turn weekly macro/investing lessons into tradable playbook cards",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router, prefix="/api", tags=["ingest"])
app.include_router(cards.router, prefix="/api", tags=["cards"])
app.include_router(alerts.router, prefix="/api", tags=["alerts"])
app.include_router(portfolio.router, prefix="/api", tags=["portfolio"])
app.include_router(similarity.router, prefix="/api", tags=["similarity"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    print("Starting up...")
    # Uncomment to auto-create tables (use migrations in production)
    # init_db()


@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "thesis-ticker-engine"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Thesis → Ticker Engine API",
        "docs": "/docs",
        "health": "/healthz"
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    uvicorn.run("app.main:app", host=host, port=port, reload=True)
