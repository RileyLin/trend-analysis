"""Named Entity Recognition service."""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class Entity:
    """Extracted entity."""
    text: str
    type: str  # Company, Commodity, Exchange, Country, Instrument, Policy_Actor, Rating_Agency
    confidence: float
    start: int
    end: int
    context: str = ""


class NERService:
    """Named Entity Recognition for financial texts (CN/EN)."""

    def __init__(self):
        """Initialize NER service with domain dictionaries."""
        self.company_patterns = self._load_company_patterns()
        self.commodity_patterns = self._load_commodity_patterns()
        self.exchange_patterns = self._load_exchange_patterns()
        self.country_patterns = self._load_country_patterns()
        self.policy_actor_patterns = self._load_policy_actor_patterns()
        self.rating_agency_patterns = self._load_rating_agency_patterns()

    def extract_entities(self, text: str, lang: str = "zh-CN") -> List[Entity]:
        """
        Extract all entities from text.

        Returns: List of Entity objects
        """
        entities = []

        # Extract each type
        entities.extend(self._extract_companies(text, lang))
        entities.extend(self._extract_commodities(text, lang))
        entities.extend(self._extract_exchanges(text, lang))
        entities.extend(self._extract_countries(text, lang))
        entities.extend(self._extract_policy_actors(text, lang))
        entities.extend(self._extract_rating_agencies(text, lang))

        # Remove duplicates and overlaps
        entities = self._remove_overlaps(entities)

        return entities

    def _extract_companies(self, text: str, lang: str) -> List[Entity]:
        """Extract company mentions."""
        entities = []

        for pattern, confidence in self.company_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entity = Entity(
                    text=match.group(),
                    type="Company",
                    confidence=confidence,
                    start=match.start(),
                    end=match.end()
                )
                entities.append(entity)

        return entities

    def _extract_commodities(self, text: str, lang: str) -> List[Entity]:
        """Extract commodity mentions."""
        entities = []

        for pattern, confidence in self.commodity_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entity = Entity(
                    text=match.group(),
                    type="Commodity",
                    confidence=confidence,
                    start=match.start(),
                    end=match.end()
                )
                entities.append(entity)

        return entities

    def _extract_exchanges(self, text: str, lang: str) -> List[Entity]:
        """Extract exchange mentions."""
        entities = []

        for pattern, confidence in self.exchange_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entity = Entity(
                    text=match.group(),
                    type="Exchange",
                    confidence=confidence,
                    start=match.start(),
                    end=match.end()
                )
                entities.append(entity)

        return entities

    def _extract_countries(self, text: str, lang: str) -> List[Entity]:
        """Extract country/region mentions."""
        entities = []

        for pattern, confidence in self.country_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entity = Entity(
                    text=match.group(),
                    type="Country",
                    confidence=confidence,
                    start=match.start(),
                    end=match.end()
                )
                entities.append(entity)

        return entities

    def _extract_policy_actors(self, text: str, lang: str) -> List[Entity]:
        """Extract policy actor mentions."""
        entities = []

        for pattern, confidence in self.policy_actor_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entity = Entity(
                    text=match.group(),
                    type="Policy_Actor",
                    confidence=confidence,
                    start=match.start(),
                    end=match.end()
                )
                entities.append(entity)

        return entities

    def _extract_rating_agencies(self, text: str, lang: str) -> List[Entity]:
        """Extract rating agency mentions."""
        entities = []

        for pattern, confidence in self.rating_agency_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entity = Entity(
                    text=match.group(),
                    type="Rating_Agency",
                    confidence=confidence,
                    start=match.start(),
                    end=match.end()
                )
                entities.append(entity)

        return entities

    def _remove_overlaps(self, entities: List[Entity]) -> List[Entity]:
        """Remove overlapping entities, keeping highest confidence."""
        if not entities:
            return []

        # Sort by start position
        entities.sort(key=lambda e: (e.start, -e.confidence))

        filtered = []
        last_end = -1

        for entity in entities:
            if entity.start >= last_end:
                filtered.append(entity)
                last_end = entity.end

        return filtered

    def _load_company_patterns(self) -> List[Tuple[str, float]]:
        """Load company name patterns with confidence scores."""
        return [
            # Quantum computing companies
            (r'\bIonQ\b', 0.95),
            (r'艾恩[Qq]', 0.95),
            (r'\bRigetti\b', 0.95),
            (r'里[盖蓋][蒂帝]', 0.90),
            (r'\bD[-\s]?Wave\b', 0.95),
            (r'\bPasqal\b', 0.95),

            # Rare earth / Graphite companies
            (r'\bMP Materials\b', 0.95),
            (r'\bLynas\b', 0.95),
            (r'\bGraphite One\b', 0.95),
            (r'石墨一[号號]', 0.95),
            (r'\bSyrah Resources\b', 0.90),
            (r'\bNorthern Graphite\b', 0.90),

            # General patterns
            (r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|Corp|Ltd|LLC|Co)\b', 0.70),
            (r'[A-Z]{2,5}(?:\s+[A-Z]{2,5})*', 0.60),  # Ticker-like patterns
        ]

    def _load_commodity_patterns(self) -> List[Tuple[str, float]]:
        """Load commodity patterns."""
        return [
            # Rare earths
            (r'稀土(?:元素)?', 0.95),
            (r'\brare\s+earth[s]?\b', 0.95),
            (r'\bREE\b', 0.90),

            # Graphite
            (r'石墨', 0.95),
            (r'\bgraphite\b', 0.95),
            (r'[天自]然石墨', 0.95),
            (r'负极材料', 0.90),

            # Gold
            (r'黄金', 0.95),
            (r'\bgold\b', 0.95),

            # Ag commodities
            (r'花生(?:期[货貨])?', 0.90),
            (r'玉米', 0.90),
            (r'大豆', 0.90),
            (r'\bcorn\b', 0.85),
            (r'\bsoybean[s]?\b', 0.85),

            # General
            (r'期[货貨]', 0.70),
            (r'\bfutures?\b', 0.70),
        ]

    def _load_exchange_patterns(self) -> List[Tuple[str, float]]:
        """Load exchange patterns."""
        return [
            (r'\bNASDAQ\b', 0.95),
            (r'\bNYSE\b', 0.95),
            (r'\bTSX\b', 0.95),
            (r'\bASX\b', 0.95),
            (r'上[海交]所', 0.95),
            (r'上期所', 0.95),
            (r'\bSHFE\b', 0.95),
            (r'芝商所', 0.95),
            (r'\bCME\b', 0.95),
            (r'\bCOMEX\b', 0.95),
            (r'大商所', 0.95),
            (r'郑商所', 0.95),
        ]

    def _load_country_patterns(self) -> List[Tuple[str, float]]:
        """Load country/region patterns."""
        return [
            (r'美[国國]', 0.95),
            (r'\bU\.?S\.?A?\b', 0.95),
            (r'\bUnited States\b', 0.95),
            (r'中[国國]', 0.95),
            (r'\bChina\b', 0.95),
            (r'欧[盟洲]', 0.95),
            (r'\bEU\b', 0.95),
            (r'\bEurope\b', 0.90),
            (r'加拿大', 0.95),
            (r'\bCanada\b', 0.95),
            (r'澳[大洲]利[亚亞]', 0.95),
            (r'\bAustralia\b', 0.95),
            (r'墨西哥', 0.95),
            (r'\bMexico\b', 0.95),
        ]

    def _load_policy_actor_patterns(self) -> List[Tuple[str, float]]:
        """Load policy actor patterns."""
        return [
            (r'美[联聯][储儲]', 0.95),
            (r'\bFed\b', 0.95),
            (r'\bFederal Reserve\b', 0.95),
            (r'[欧歐]洲央行', 0.95),
            (r'\bECB\b', 0.95),
            (r'人民[银銀]行', 0.95),
            (r'\bPBOC\b', 0.90),
            (r'[国國][务務]院', 0.90),
            (r'商[务務]部', 0.90),
            (r'[财財][政経]部', 0.90),
        ]

    def _load_rating_agency_patterns(self) -> List[Tuple[str, float]]:
        """Load rating agency patterns."""
        return [
            (r'\bMoody\'?s\b', 0.95),
            (r'穆迪', 0.95),
            (r'\bS&P\b', 0.95),
            (r'\bStandard & Poor\'?s\b', 0.95),
            (r'标[准準]普[尔爾]', 0.95),
            (r'\bFitch\b', 0.95),
            (r'惠[誉譽]', 0.95),
        ]
