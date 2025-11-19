"""Tests for NER service."""

import pytest
from app.services.ner import NERService


class TestNERService:
    """Test Named Entity Recognition."""

    @pytest.fixture
    def ner_service(self):
        """Create NER service."""
        return NERService()

    def test_extract_companies(self, ner_service):
        """Test company extraction."""
        text = "IonQ and Rigetti are quantum computing companies"
        entities = ner_service.extract_entities(text, "en-US")

        company_entities = [e for e in entities if e.type == "Company"]
        assert len(company_entities) >= 1

    def test_extract_commodities(self, ner_service):
        """Test commodity extraction."""
        text = "稀土和石墨是关键材料"
        entities = ner_service.extract_entities(text, "zh-CN")

        commodity_entities = [e for e in entities if e.type == "Commodity"]
        assert len(commodity_entities) >= 1

    def test_extract_exchanges(self, ner_service):
        """Test exchange extraction."""
        text = "NASDAQ and NYSE listings"
        entities = ner_service.extract_entities(text, "en-US")

        exchange_entities = [e for e in entities if e.type == "Exchange"]
        assert len(exchange_entities) >= 1

    def test_extract_mixed_language(self, ner_service):
        """Test mixed language extraction."""
        text = "IONQ在NASDAQ上市，主要投资于量子计算"
        entities = ner_service.extract_entities(text, "zh-CN")

        assert len(entities) > 0
