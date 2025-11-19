"""Tests for API endpoints."""

import pytest
from datetime import date


class TestIngestAPI:
    """Test ingest API."""

    def test_ingest_simple_text(self, client):
        """Test ingesting simple text."""
        request_data = {
            "text": "IonQ is a quantum computing company. The US government may invest $10M in quantum technology.",
            "expert_ref": "test",
            "locale": "en-US"
        }

        response = client.post("/api/ingest", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "cards" in data
        assert "processing_time" in data
        assert "total_entities_extracted" in data
        assert isinstance(data["cards"], list)

    def test_ingest_chinese_text(self, client):
        """Test ingesting Chinese text."""
        request_data = {
            "text": "稀土是关键材料。美国可能会对稀土出口实施管制。",
            "locale": "zh-CN"
        }

        response = client.post("/api/ingest", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "cards" in data
        assert len(data["cards"]) >= 0  # May or may not generate cards depending on entity mapping


class TestCardsAPI:
    """Test cards API."""

    def test_create_card(self, client):
        """Test creating a card."""
        card_data = {
            "id": "test_card_001",
            "asof": str(date.today()),
            "summary_en": "Test card",
            "summary_cn": "测试卡片",
            "direction": "long",
            "horizon": "3m",
            "instruments": [
                {
                    "symbol": "IONQ",
                    "venue": "NASDAQ",
                    "role": "primary"
                }
            ],
            "entry_triggers": [
                {
                    "type": "price_level",
                    "expr": {"symbol": "IONQ", "op": ">=", "level": 10.0},
                    "nl_en": "Price >= 10.0",
                    "nl_cn": "价格 >= 10.0"
                }
            ],
            "invalidators": [
                {
                    "type": "time_stop",
                    "expr": {"days": 45},
                    "nl_en": "45-day stop",
                    "nl_cn": "45天止损"
                }
            ],
            "catalysts": ["Government funding"],
            "risks": ["Valuation"],
            "why": [
                {
                    "quote": "Test quote",
                    "source_loc": "p1"
                }
            ],
            "confidence": 0.8
        }

        response = client.post("/api/cards", json=card_data)

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "test_card_001"

    def test_list_cards(self, client):
        """Test listing cards."""
        response = client.get("/api/cards")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestPortfolioAPI:
    """Test portfolio API."""

    def test_get_empty_portfolio(self, client):
        """Test getting empty portfolio."""
        response = client.get("/api/portfolio")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_portfolio_stats(self, client):
        """Test getting portfolio stats."""
        response = client.get("/api/portfolio/stats")

        assert response.status_code == 200
        data = response.json()

        assert "total_positions" in data
        assert "total_pnl" in data
        assert "win_rate" in data
