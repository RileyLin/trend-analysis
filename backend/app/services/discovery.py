"""Discovery engine - find similar-logic tickers."""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import numpy as np
from sentence_transformers import SentenceTransformer

from app.models.instrument import Instrument
from app.models.thesis import Thesis
from app.models.similarity import SimilarityCandidate


class DiscoveryEngine:
    """Find similar tickers based on thesis logic."""

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
        # Load multilingual embedding model
        try:
            self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        except Exception as e:
            print(f"Warning: Could not load embedding model: {e}")
            self.embedding_model = None

    def find_similar_tickers(
        self,
        card_id: str,
        top_k: int = 10,
        min_score: float = 0.5
    ) -> List[SimilarityCandidate]:
        """
        Find similar tickers for a card.

        Args:
            card_id: Thesis card ID
            top_k: Number of candidates to return
            min_score: Minimum similarity score

        Returns: List of SimilarityCandidate objects
        """
        # Get thesis
        thesis = self.db.query(Thesis).filter(Thesis.id == card_id).first()

        if not thesis:
            return []

        # Build feature vector for this card
        card_features = self._extract_card_features(thesis)

        # Get candidate pool
        candidate_instruments = self._get_candidate_pool(thesis)

        # Score each candidate
        candidates = []

        for instrument in candidate_instruments:
            score, explanation = self._score_candidate(
                card_features,
                instrument,
                thesis
            )

            if score >= min_score:
                # Create bilingual explanation
                explanation_cn, explanation_en = self._generate_explanations(
                    card_features,
                    instrument,
                    score
                )

                candidate = SimilarityCandidate(
                    card_id=card_id,
                    candidate_symbol=instrument.symbol,
                    score=score,
                    explanation=explanation,
                    explanation_cn=explanation_cn,
                    explanation_en=explanation_en
                )

                candidates.append(candidate)

        # Sort by score
        candidates.sort(key=lambda c: c.score, reverse=True)

        # Save top candidates to DB
        for candidate in candidates[:top_k]:
            self.db.add(candidate)

        self.db.commit()

        return candidates[:top_k]

    def _extract_card_features(self, thesis: Thesis) -> Dict:
        """Extract feature vector from a card."""
        features = {
            'themes': [],
            'catalysts': [],
            'geo': [],
            'text': '',
            'embedding': None
        }

        # Extract text for embedding
        text_parts = []

        if thesis.summary_en:
            text_parts.append(thesis.summary_en)

        if thesis.summary_cn:
            text_parts.append(thesis.summary_cn)

        # Add quotes
        for quote in thesis.quotes:
            text_parts.append(quote.quote)

        features['text'] = " ".join(text_parts)

        # Generate embedding
        if self.embedding_model and features['text']:
            try:
                embedding = self.embedding_model.encode(features['text'])
                features['embedding'] = embedding
            except Exception as e:
                print(f"Error generating embedding: {e}")

        # Extract themes/tags from instruments metadata
        for thesis_inst in thesis.instruments:
            inst = thesis_inst.instrument
            meta = inst.meta or {}

            if 'themes' in meta:
                features['themes'].extend(meta['themes'])

            if 'catalysts' in meta:
                features['catalysts'].extend(meta['catalysts'])

            if 'geo' in meta:
                features['geo'].append(meta['geo'])

        return features

    def _get_candidate_pool(self, thesis: Thesis) -> List[Instrument]:
        """Get pool of candidate instruments."""
        # For MVP, get all instruments excluding those already in the thesis
        thesis_symbols = [ti.instrument.symbol for ti in thesis.instruments]

        candidates = self.db.query(Instrument).filter(
            Instrument.asset_class.in_(['equity', 'etf']),
            ~Instrument.symbol.in_(thesis_symbols)
        ).limit(1000).all()

        return candidates

    def _score_candidate(
        self,
        card_features: Dict,
        instrument: Instrument,
        thesis: Thesis
    ) -> tuple[float, str]:
        """
        Score a candidate instrument.

        Returns: (score, explanation)
        """
        score = 0.0
        explanations = []

        # 1. Text similarity (if embeddings available)
        if card_features.get('embedding') is not None and instrument.meta:
            inst_text = f"{instrument.display_name_en} {instrument.meta.get('sector', '')}"

            try:
                inst_embedding = self.embedding_model.encode(inst_text)

                # Cosine similarity
                text_sim = float(np.dot(card_features['embedding'], inst_embedding) / (
                    np.linalg.norm(card_features['embedding']) * np.linalg.norm(inst_embedding)
                ))

                score += text_sim * 0.5  # 50% weight
                explanations.append(f"text_sim={text_sim:.2f}")
            except Exception:
                pass

        # 2. Feature overlap
        inst_meta = instrument.meta or {}

        # Theme overlap
        inst_themes = set(inst_meta.get('themes', []))
        card_themes = set(card_features.get('themes', []))

        if inst_themes and card_themes:
            theme_overlap = len(inst_themes & card_themes) / max(len(card_themes), 1)
            score += theme_overlap * 0.3  # 30% weight
            if theme_overlap > 0:
                explanations.append(f"theme_overlap={list(inst_themes & card_themes)}")

        # Catalyst overlap
        inst_catalysts = set(inst_meta.get('catalysts', []))
        card_catalysts = set(card_features.get('catalysts', []))

        if inst_catalysts and card_catalysts:
            catalyst_overlap = len(inst_catalysts & card_catalysts) / max(len(card_catalysts), 1)
            score += catalyst_overlap * 0.2  # 20% weight
            if catalyst_overlap > 0:
                explanations.append(f"catalyst_overlap={list(inst_catalysts & card_catalysts)}")

        explanation = ", ".join(explanations) if explanations else "no_match"

        return min(score, 1.0), explanation

    def _generate_explanations(
        self,
        card_features: Dict,
        instrument: Instrument,
        score: float
    ) -> tuple[str, str]:
        """Generate bilingual explanations."""
        inst_meta = instrument.meta or {}

        themes = inst_meta.get('themes', [])
        catalysts = inst_meta.get('catalysts', [])
        geo = inst_meta.get('geo', '')

        # English
        explanation_en = f"Matched on: similarity={score:.2f}"
        if themes:
            explanation_en += f", themes={','.join(themes[:2])}"
        if catalysts:
            explanation_en += f", catalysts={','.join(catalysts[:2])}"
        if geo:
            explanation_en += f", geo={geo}"

        # Chinese (simple translation)
        explanation_cn = f"匹配因为: 相似度={score:.2f}"
        if themes:
            explanation_cn += f", 主题={','.join(themes[:2])}"
        if catalysts:
            explanation_cn += f", 催化={','.join(catalysts[:2])}"
        if geo:
            explanation_cn += f", 地区={geo}"

        return explanation_cn, explanation_en
