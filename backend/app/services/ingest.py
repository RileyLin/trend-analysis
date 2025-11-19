"""Ingest service - processes transcripts and generates draft cards."""

import time
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from datetime import date

from app.services.language_utils import LanguageDetector, TextCleaner
from app.services.ner import NERService, Entity
from app.services.ticker_mapper import TickerMapper
from app.services.translation import TranslationService
from app.schemas.ingest import DraftCard, EntityCandidate, IngestResponse
from app.schemas.card import InstrumentRef, TriggerExpr, QuoteReference


class IngestService:
    """
    Ingest transcript and generate draft playbook cards.

    Process:
    1. Detect language and segment text
    2. Extract entities (NER)
    3. Map entities to tickers
    4. Cluster related statements into thesis cards
    5. Generate entry/exit/invalidators
    6. Translate to both languages
    """

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
        self.lang_detector = LanguageDetector()
        self.text_cleaner = TextCleaner()
        self.ner_service = NERService()
        self.ticker_mapper = TickerMapper(db)
        self.translation_service = TranslationService(db)

    def ingest_transcript(self, text: str, expert_ref: str = None) -> IngestResponse:
        """
        Ingest transcript and generate draft cards.

        Args:
            text: Transcript text (can be CN/EN/mixed)
            expert_ref: Optional reference to expert/source

        Returns: IngestResponse with draft cards
        """
        start_time = time.time()

        # 1. Clean text
        text = self.text_cleaner.clean_text(text)

        # 2. Detect language
        primary_lang = self.lang_detector.detect_language(text)

        # 3. Split into sentences
        sentences = self.lang_detector.split_sentences(text, primary_lang)

        # 4. Extract entities
        entities = self.ner_service.extract_entities(text, primary_lang)

        # 5. Map entities to tickers
        entity_candidates = []
        for entity in entities:
            ticker_candidates = self.ticker_mapper.map_entity_to_tickers(
                entity.text,
                entity.type
            )

            entity_candidate = EntityCandidate(
                text=entity.text,
                type=entity.type,
                confidence=entity.confidence,
                ticker_candidates=[
                    {
                        'symbol': tc.symbol,
                        'venue': tc.venue,
                        'confidence': tc.confidence,
                        'display_name_en': tc.display_name_en,
                        'display_name_cn': tc.display_name_cn
                    }
                    for tc in ticker_candidates
                ]
            )
            entity_candidates.append(entity_candidate)

        # 6. Cluster statements into thesis cards
        draft_cards = self._generate_draft_cards(
            text=text,
            sentences=sentences,
            entities=entities,
            entity_candidates=entity_candidates,
            primary_lang=primary_lang,
            expert_ref=expert_ref
        )

        # 7. Calculate processing time
        processing_time = time.time() - start_time

        return IngestResponse(
            cards=draft_cards,
            processing_time=processing_time,
            total_entities_extracted=len(entities),
            language_detected=primary_lang
        )

    def _generate_draft_cards(
        self,
        text: str,
        sentences: List[str],
        entities: List[Entity],
        entity_candidates: List[EntityCandidate],
        primary_lang: str,
        expert_ref: str = None
    ) -> List[DraftCard]:
        """Generate draft cards from extracted entities."""
        draft_cards = []

        # Group entities by ticker/theme
        ticker_groups = self._group_entities_by_ticker(entity_candidates)

        card_id = 0
        for ticker, group_entities in ticker_groups.items():
            card_id += 1

            # Get primary instrument
            primary_instrument = self._get_primary_instrument(group_entities)
            if not primary_instrument:
                continue

            # Find relevant quotes
            quotes = self._find_relevant_quotes(sentences, group_entities, max_quotes=3)

            # Generate summary (bilingual)
            summary_en, summary_cn = self._generate_summary(
                primary_instrument,
                group_entities,
                quotes,
                primary_lang
            )

            # Generate default triggers and invalidators
            entry_triggers, invalidators = self._generate_default_triggers(
                primary_instrument,
                primary_lang
            )

            # Determine direction (simple heuristic)
            direction = self._determine_direction(quotes)

            # Extract catalysts and risks
            catalysts, risks = self._extract_catalysts_and_risks(quotes)

            # Create draft card
            draft_card = DraftCard(
                id=f"card_{date.today().strftime('%Y%m%d')}_{card_id:03d}",
                asof=date.today(),
                summary_cn=summary_cn,
                summary_en=summary_en,
                direction=direction,
                horizon="3m",  # Default
                instruments=[primary_instrument],
                entry_triggers=entry_triggers,
                invalidators=invalidators,
                catalysts=catalysts,
                risks=risks,
                why=[
                    QuoteReference(
                        quote=q['text'],
                        source_loc=f"p{q['index']}",
                        gloss_cn=q['text'] if primary_lang == "zh-CN" else None,
                        gloss_en=q['text'] if primary_lang == "en-US" else None
                    )
                    for q in quotes
                ],
                confidence=0.75,  # Default confidence
                extraction_confidence=0.75,
                entities=group_entities
            )

            draft_cards.append(draft_card)

        return draft_cards

    def _group_entities_by_ticker(self, entity_candidates: List[EntityCandidate]) -> Dict[str, List[EntityCandidate]]:
        """Group entities by ticker symbol."""
        groups = {}

        for entity in entity_candidates:
            if not entity.ticker_candidates:
                continue

            # Use top ticker candidate
            top_ticker = entity.ticker_candidates[0]['symbol']

            if top_ticker not in groups:
                groups[top_ticker] = []

            groups[top_ticker].append(entity)

        return groups

    def _get_primary_instrument(self, entities: List[EntityCandidate]) -> InstrumentRef:
        """Get primary instrument from entity group."""
        # Find entity with highest confidence ticker
        best_entity = None
        best_confidence = 0

        for entity in entities:
            if entity.ticker_candidates:
                tc = entity.ticker_candidates[0]
                if tc['confidence'] > best_confidence:
                    best_confidence = tc['confidence']
                    best_entity = entity

        if not best_entity:
            return None

        tc = best_entity.ticker_candidates[0]

        return InstrumentRef(
            symbol=tc['symbol'],
            venue=tc['venue'],
            role='primary',
            display_name_en=tc['display_name_en'],
            display_name_cn=tc['display_name_cn']
        )

    def _find_relevant_quotes(
        self,
        sentences: List[str],
        entities: List[EntityCandidate],
        max_quotes: int = 3
    ) -> List[Dict]:
        """Find relevant quotes containing entities."""
        entity_texts = [e.text.lower() for e in entities]
        quotes = []

        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()

            # Check if sentence mentions any entity
            for entity_text in entity_texts:
                if entity_text in sentence_lower:
                    quotes.append({
                        'text': sentence,
                        'index': i,
                        'entities': [entity_text]
                    })
                    break

        # Return top quotes
        return quotes[:max_quotes]

    def _generate_summary(
        self,
        instrument: InstrumentRef,
        entities: List[EntityCandidate],
        quotes: List[Dict],
        primary_lang: str
    ) -> Tuple[str, str]:
        """Generate bilingual summary."""
        # Simple summary template
        symbol = instrument.symbol

        if primary_lang == "zh-CN":
            summary_cn = f"关注 {symbol}，基于相关催化剂和市场机会"
            summary_en = self.translation_service.translate(summary_cn, "zh-CN", "en-US")
        else:
            summary_en = f"Watch {symbol} based on relevant catalysts and market opportunities"
            summary_cn = self.translation_service.translate(summary_en, "en-US", "zh-CN")

        return summary_en, summary_cn

    def _generate_default_triggers(
        self,
        instrument: InstrumentRef,
        primary_lang: str
    ) -> Tuple[List[TriggerExpr], List[TriggerExpr]]:
        """Generate default entry triggers and invalidators."""
        # Entry trigger: Price level (placeholder - user should edit)
        entry_trigger = TriggerExpr(
            type="price_level",
            expr={"symbol": instrument.symbol, "op": ">=", "level": 10.0},
            nl_cn="价格 >= 10.0",
            nl_en="Price >= 10.0"
        )

        # Invalidator: Time stop (45 days default)
        invalidator = TriggerExpr(
            type="time_stop",
            expr={"days": 45},
            nl_cn="45天止损",
            nl_en="45-day time stop"
        )

        return [entry_trigger], [invalidator]

    def _determine_direction(self, quotes: List[Dict]) -> str:
        """Determine trade direction from quotes (simple heuristic)."""
        # Look for bullish/bearish keywords
        text = " ".join([q['text'].lower() for q in quotes])

        bullish_keywords = ['上涨', '看涨', '买入', 'buy', 'long', 'bullish', 'upside']
        bearish_keywords = ['下跌', '看跌', '卖出', 'sell', 'short', 'bearish', 'downside']

        bullish_count = sum(1 for kw in bullish_keywords if kw in text)
        bearish_count = sum(1 for kw in bearish_keywords if kw in text)

        if bullish_count > bearish_count:
            return "long"
        elif bearish_count > bullish_count:
            return "short"
        else:
            return "long"  # Default

    def _extract_catalysts_and_risks(self, quotes: List[Dict]) -> Tuple[List[str], List[str]]:
        """Extract catalysts and risks from quotes."""
        catalysts = []
        risks = []

        catalyst_keywords = ['补贴', '资助', 'subsidy', 'grant', '政策', 'policy', '评级', 'rating']
        risk_keywords = ['风险', 'risk', '不确定', 'uncertain', '延迟', 'delay']

        for quote in quotes:
            text = quote['text'].lower()

            has_catalyst = any(kw in text for kw in catalyst_keywords)
            has_risk = any(kw in text for kw in risk_keywords)

            if has_catalyst:
                catalysts.append(quote['text'][:50] + "...")
            if has_risk:
                risks.append(quote['text'][:50] + "...")

        return catalysts[:3], risks[:2]
