"""Translation service with glossary support."""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.glossary import Glossary, TranslationMemory
import re


class TranslationService:
    """Bilingual translation with glossary pinning."""

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
        self.glossary = self._load_glossary()
        self.do_not_translate = self._load_do_not_translate_patterns()

    def translate(self, text: str, src_lang: str, dst_lang: str) -> str:
        """
        Translate text with glossary pinning.

        Args:
            text: Source text
            src_lang: Source language (zh-CN or en-US)
            dst_lang: Destination language (zh-CN or en-US)

        Returns: Translated text
        """
        if src_lang == dst_lang:
            return text

        # Check translation memory first
        tm_result = self._check_translation_memory(text, src_lang, dst_lang)
        if tm_result:
            return tm_result

        # Apply glossary substitutions
        protected_terms = {}
        text_with_placeholders = self._protect_glossary_terms(text, src_lang, protected_terms)

        # Protect numbers and tickers
        text_with_placeholders = self._protect_numbers_and_tickers(text_with_placeholders, protected_terms)

        # Simple rule-based translation (in production, use a real MT service)
        translated = self._simple_translate(text_with_placeholders, src_lang, dst_lang)

        # Restore protected terms
        translated = self._restore_protected_terms(translated, protected_terms)

        # Save to translation memory
        self._save_to_translation_memory(text, translated, src_lang, dst_lang)

        return translated

    def _protect_glossary_terms(self, text: str, src_lang: str, protected_terms: dict) -> str:
        """Replace glossary terms with placeholders."""
        placeholder_id = 0

        for term_key, term_data in self.glossary.items():
            if not term_data.get('pinned'):
                continue

            # Get source language term
            src_term = term_data.get('cn' if src_lang == 'zh-CN' else 'en')
            if not src_term:
                continue

            # Check aliases too
            terms_to_check = [src_term] + term_data.get('aliases', [])

            for term in terms_to_check:
                if term in text:
                    placeholder = f"__TERM_{placeholder_id}__"
                    protected_terms[placeholder] = term
                    text = text.replace(term, placeholder)
                    placeholder_id += 1

        return text

    def _protect_numbers_and_tickers(self, text: str, protected_terms: dict) -> str:
        """Protect numbers and ticker symbols."""
        placeholder_id = len(protected_terms)

        # Protect numbers
        number_pattern = r'\b\d+\.?\d*\s*[%％]?'
        for match in re.finditer(number_pattern, text):
            placeholder = f"__NUM_{placeholder_id}__"
            protected_terms[placeholder] = match.group()
            text = text.replace(match.group(), placeholder, 1)
            placeholder_id += 1

        # Protect ticker symbols (all caps, 2-5 letters)
        ticker_pattern = r'\b[A-Z]{2,5}\b'
        for match in re.finditer(ticker_pattern, text):
            placeholder = f"__TICK_{placeholder_id}__"
            protected_terms[placeholder] = match.group()
            text = text.replace(match.group(), placeholder, 1)
            placeholder_id += 1

        return text

    def _restore_protected_terms(self, text: str, protected_terms: dict) -> str:
        """Restore protected terms from placeholders."""
        for placeholder, original in protected_terms.items():
            text = text.replace(placeholder, original)
        return text

    def _simple_translate(self, text: str, src_lang: str, dst_lang: str) -> str:
        """
        Simple rule-based translation.

        In production, replace with actual MT service (OpenAI, Google Translate, etc.)
        """
        # For MVP, use a simple dictionary-based approach
        if src_lang == "zh-CN" and dst_lang == "en-US":
            return self._cn_to_en(text)
        elif src_lang == "en-US" and dst_lang == "zh-CN":
            return self._en_to_cn(text)
        else:
            return text

    def _cn_to_en(self, text: str) -> str:
        """Simple Chinese to English translation."""
        translations = {
            '保证金': 'margin',
            '上调': 'increase',
            '下调': 'decrease',
            '评级': 'rating',
            '展望': 'outlook',
            '负面': 'negative',
            '正面': 'positive',
            '补贴': 'subsidy',
            '资助': 'grant',
            '入股': 'equity stake',
            '出口管制': 'export controls',
            '逢低': 'buy the dip',
            '回调': 'pullback',
            '阶段性': 'phase',
            '调整': 'correction',
            '价格': 'price',
            '水平': 'level',
            '触发': 'trigger',
            '失效': 'invalidate',
        }

        for cn, en in translations.items():
            text = text.replace(cn, en)

        return text

    def _en_to_cn(self, text: str) -> str:
        """Simple English to Chinese translation."""
        translations = {
            'margin': '保证金',
            'increase': '上调',
            'decrease': '下调',
            'rating': '评级',
            'outlook': '展望',
            'negative': '负面',
            'positive': '正面',
            'subsidy': '补贴',
            'grant': '资助',
            'equity stake': '入股',
            'export controls': '出口管制',
            'buy the dip': '逢低',
            'pullback': '回调',
            'phase': '阶段性',
            'correction': '调整',
            'price': '价格',
            'level': '水平',
            'trigger': '触发',
            'invalidate': '失效',
        }

        for en, cn in translations.items():
            text = text.replace(en, cn)

        return text

    def _check_translation_memory(self, text: str, src_lang: str, dst_lang: str) -> Optional[str]:
        """Check if translation exists in memory."""
        tm_entry = self.db.query(TranslationMemory).filter(
            TranslationMemory.src_text == text,
            TranslationMemory.src_lang == src_lang,
            TranslationMemory.dst_lang == dst_lang
        ).first()

        if tm_entry:
            # Update hit count
            tm_entry.hits += 1
            self.db.commit()
            return tm_entry.dst_text

        return None

    def _save_to_translation_memory(self, src_text: str, dst_text: str, src_lang: str, dst_lang: str):
        """Save translation to memory."""
        # Check if already exists
        existing = self.db.query(TranslationMemory).filter(
            TranslationMemory.src_text == src_text,
            TranslationMemory.src_lang == src_lang,
            TranslationMemory.dst_lang == dst_lang
        ).first()

        if not existing:
            tm_entry = TranslationMemory(
                src_text=src_text,
                dst_text=dst_text,
                src_lang=src_lang,
                dst_lang=dst_lang,
                domain='finance'
            )
            self.db.add(tm_entry)
            self.db.commit()

    def _load_glossary(self) -> Dict[str, dict]:
        """Load glossary from database."""
        glossary_entries = self.db.query(Glossary).all()

        glossary = {}
        for entry in glossary_entries:
            glossary[entry.key] = {
                'cn': entry.cn,
                'en': entry.en,
                'pinned': entry.pinned,
                'aliases': entry.aliases or []
            }

        return glossary

    def _load_do_not_translate_patterns(self) -> List[str]:
        """Load patterns that should never be translated."""
        return [
            r'\b[A-Z]{2,5}\b',  # Ticker symbols
            r'\d+\.?\d*\s*[%％]?',  # Numbers with optional percent
            r'\$\d+',  # Dollar amounts
            r'¥\d+',  # Yuan amounts
            r'€\d+',  # Euro amounts
        ]
