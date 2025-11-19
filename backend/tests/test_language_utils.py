"""Tests for language utilities."""

import pytest
from app.services.language_utils import LanguageDetector, TextCleaner


class TestLanguageDetector:
    """Test language detection."""

    def test_detect_chinese(self):
        """Test Chinese language detection."""
        text = "这是一个关于稀土的投资机会"
        lang = LanguageDetector.detect_language(text)
        assert lang == "zh-CN"

    def test_detect_english(self):
        """Test English language detection."""
        text = "This is an investment opportunity in rare earths"
        lang = LanguageDetector.detect_language(text)
        assert lang == "en-US"

    def test_detect_mixed(self):
        """Test mixed language detection."""
        text = "IonQ 是一个量子计算公司 with strong potential"
        lang = LanguageDetector.detect_language(text)
        assert lang in ["zh-CN", "mixed"]

    def test_split_sentences_chinese(self):
        """Test Chinese sentence splitting."""
        text = "第一句话。第二句话！第三句话？"
        sentences = LanguageDetector.split_sentences(text, "zh-CN")
        assert len(sentences) == 3

    def test_split_sentences_english(self):
        """Test English sentence splitting."""
        text = "First sentence. Second sentence! Third sentence?"
        sentences = LanguageDetector.split_sentences(text, "en-US")
        assert len(sentences) == 3


class TestTextCleaner:
    """Test text cleaning."""

    def test_clean_text(self):
        """Test basic text cleaning."""
        text = "  This   has   extra   spaces  \n\n\n  and newlines  "
        cleaned = TextCleaner.clean_text(text)
        assert "   " not in cleaned
        assert cleaned.strip() == cleaned

    def test_normalize_numbers(self):
        """Test number normalization."""
        text = "价格是１２３．４５"
        normalized = TextCleaner.normalize_numbers(text)
        assert "123.45" in normalized

    def test_extract_numbers(self):
        """Test number extraction."""
        text = "Price is 123.45 or 50%"
        numbers = TextCleaner.extract_numbers(text)
        assert 123.45 in numbers or 123 in numbers
        assert 50 in numbers or 0.5 in numbers
