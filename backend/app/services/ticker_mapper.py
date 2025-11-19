"""Ticker mapping service - maps entities to tradable instruments."""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.models.instrument import Instrument
import re


@dataclass
class TickerCandidate:
    """Ticker candidate with confidence score."""
    symbol: str
    venue: str
    display_name_en: str
    display_name_cn: str
    confidence: float
    asset_class: str
    meta: dict


class TickerMapper:
    """Map entity names to ticker symbols."""

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
        self.symbol_map = self._load_symbol_map()
        self.alias_map = self._load_alias_map()

    def map_entity_to_tickers(self, entity_text: str, entity_type: str) -> List[TickerCandidate]:
        """
        Map an entity to ticker candidates.

        Returns: List of TickerCandidate objects sorted by confidence
        """
        candidates = []

        # Normalize entity text
        normalized = self._normalize_entity(entity_text)

        # Try exact match first
        if normalized in self.symbol_map:
            candidates.append(self._create_candidate(normalized, confidence=0.95))

        # Try alias match
        if normalized in self.alias_map:
            for symbol in self.alias_map[normalized]:
                candidates.append(self._create_candidate(symbol, confidence=0.90))

        # Try fuzzy match for company names
        if entity_type == "Company" and not candidates:
            fuzzy_matches = self._fuzzy_match_company(normalized)
            candidates.extend(fuzzy_matches)

        # Try commodity to ETF/future mapping
        if entity_type == "Commodity":
            commodity_matches = self._map_commodity_to_instruments(normalized)
            candidates.extend(commodity_matches)

        # Sort by confidence
        candidates.sort(key=lambda c: c.confidence, reverse=True)

        # Return top 3
        return candidates[:3]

    def _normalize_entity(self, text: str) -> str:
        """Normalize entity text for matching."""
        # Remove common suffixes
        text = re.sub(r'\s+(Inc|Corp|Ltd|LLC|Co)\b', '', text, flags=re.IGNORECASE)

        # Convert to lowercase
        text = text.lower().strip()

        return text

    def _create_candidate(self, symbol: str, confidence: float) -> TickerCandidate:
        """Create a ticker candidate from symbol."""
        if symbol not in self.symbol_map:
            return None

        info = self.symbol_map[symbol]

        return TickerCandidate(
            symbol=info['symbol'],
            venue=info['venue'],
            display_name_en=info['display_name_en'],
            display_name_cn=info['display_name_cn'],
            confidence=confidence,
            asset_class=info['asset_class'],
            meta=info.get('meta', {})
        )

    def _fuzzy_match_company(self, name: str) -> List[TickerCandidate]:
        """Fuzzy match company name to tickers."""
        candidates = []

        # Simple substring matching
        for key, info in self.symbol_map.items():
            if info['asset_class'] not in ['equity', 'etf']:
                continue

            display_name = info['display_name_en'].lower()

            if name in display_name or display_name in name:
                confidence = 0.70  # Lower confidence for fuzzy
                candidate = TickerCandidate(
                    symbol=info['symbol'],
                    venue=info['venue'],
                    display_name_en=info['display_name_en'],
                    display_name_cn=info['display_name_cn'],
                    confidence=confidence,
                    asset_class=info['asset_class'],
                    meta=info.get('meta', {})
                )
                candidates.append(candidate)

        return candidates

    def _map_commodity_to_instruments(self, commodity: str) -> List[TickerCandidate]:
        """Map commodity to relevant ETFs/futures."""
        commodity_map = {
            '稀土': ['MP', 'LYC'],
            'rare earth': ['MP', 'LYC'],
            '石墨': ['SYR', 'NGC'],
            'graphite': ['SYR', 'NGC'],
            '黄金': ['GLD', 'GC=F'],
            'gold': ['GLD', 'GC=F'],
            '花生': ['CORN', 'DBA'],  # Proxy
        }

        symbols = commodity_map.get(commodity, [])
        candidates = []

        for symbol in symbols:
            if symbol in self.symbol_map:
                candidates.append(self._create_candidate(symbol, confidence=0.85))

        return candidates

    def _load_symbol_map(self) -> Dict[str, dict]:
        """Load symbol mapping from database."""
        # Query all instruments
        instruments = self.db.query(Instrument).all()

        symbol_map = {}

        for inst in instruments:
            key = inst.symbol.lower()
            symbol_map[key] = {
                'symbol': inst.symbol,
                'venue': inst.venue,
                'display_name_en': inst.display_name_en or inst.symbol,
                'display_name_cn': inst.display_name_cn or inst.symbol,
                'asset_class': inst.asset_class,
                'meta': inst.meta or {}
            }

        return symbol_map

    def _load_alias_map(self) -> Dict[str, List[str]]:
        """Load alias mapping."""
        # Hardcoded aliases (could be from DB in production)
        return {
            'ionq': ['ionq'],
            '艾恩q': ['ionq'],
            'rigetti': ['rgti'],
            '里盖蒂': ['rgti'],
            'graphite one': ['gph'],
            '石墨一号': ['gph'],
            'mp materials': ['mp'],
            'lynas': ['lyc'],
            'syrah resources': ['syr'],
        }
