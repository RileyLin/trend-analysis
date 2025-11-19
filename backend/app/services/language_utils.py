"""Language detection and text processing utilities."""

import re
from typing import List, Tuple
import jieba
from langdetect import detect, LangDetectException


class LanguageDetector:
    """Detect language and segment text."""

    @staticmethod
    def detect_language(text: str) -> str:
        """
        Detect primary language of text.

        Returns: 'zh-CN', 'en-US', or 'mixed'
        """
        if not text or len(text.strip()) < 10:
            return "en-US"

        # Count Chinese characters
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text.replace(" ", "").replace("\n", ""))

        if total_chars == 0:
            return "en-US"

        chinese_ratio = chinese_chars / total_chars

        if chinese_ratio > 0.3:
            return "zh-CN"
        elif chinese_ratio > 0.05:
            return "mixed"
        else:
            return "en-US"

    @staticmethod
    def segment_chinese(text: str) -> List[str]:
        """Segment Chinese text using Jieba."""
        return list(jieba.cut(text))

    @staticmethod
    def split_sentences(text: str, lang: str = "en-US") -> List[str]:
        """
        Split text into sentences based on language.

        For Chinese: Split on Chinese punctuation (。！？；)
        For English: Split on standard punctuation (.!?;)
        """
        if lang == "zh-CN" or lang == "mixed":
            # Chinese sentence splitters (full-width punctuation)
            sentences = re.split(r'[。！？；\n]+', text)
        else:
            # English sentence splitters
            sentences = re.split(r'[.!?;\n]+', text)

        # Clean and filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    @staticmethod
    def detect_per_chunk(text: str, chunk_size: int = 500) -> List[Tuple[str, str]]:
        """
        Detect language per chunk of text.

        Returns: List of (chunk_text, language) tuples
        """
        chunks = []
        lines = text.split("\n")
        current_chunk = ""

        for line in lines:
            if len(current_chunk) + len(line) > chunk_size and current_chunk:
                lang = LanguageDetector.detect_language(current_chunk)
                chunks.append((current_chunk, lang))
                current_chunk = line
            else:
                current_chunk += "\n" + line if current_chunk else line

        # Add last chunk
        if current_chunk:
            lang = LanguageDetector.detect_language(current_chunk)
            chunks.append((current_chunk, lang))

        return chunks


class ChineseProcessor:
    """Process Chinese text."""

    @staticmethod
    def simplify_traditional(text: str) -> str:
        """Convert traditional Chinese to simplified (if needed)."""
        try:
            from opencc import OpenCC
            cc = OpenCC('t2s')  # Traditional to Simplified
            return cc.convert(text)
        except ImportError:
            # If opencc not available, return as-is
            return text
        except Exception:
            return text

    @staticmethod
    def normalize_punctuation(text: str) -> str:
        """Normalize Chinese punctuation to full-width."""
        replacements = {
            ',': '，',
            ';': '；',
            ':': '：',
            '!': '！',
            '?': '？',
            '(': '（',
            ')': '）',
        }

        for eng, chn in replacements.items():
            text = text.replace(eng, chn)

        return text


class TextCleaner:
    """Clean and normalize text."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Basic text cleaning."""
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)

        # Remove multiple newlines
        text = re.sub(r'\n+', '\n', text)

        # Strip
        text = text.strip()

        return text

    @staticmethod
    def normalize_numbers(text: str) -> str:
        """Normalize numbers to half-width."""
        # Convert full-width numbers to half-width
        full_to_half = str.maketrans(
            '０１２３４５６７８９',
            '0123456789'
        )
        return text.translate(full_to_half)

    @staticmethod
    def extract_numbers(text: str) -> List[float]:
        """Extract all numbers from text."""
        # Match numbers with optional decimal points, commas, and units
        pattern = r'[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?'
        matches = re.findall(pattern, text)
        numbers = []

        for match in matches:
            try:
                if isinstance(match, tuple):
                    match = match[0] if match[0] else "0"
                numbers.append(float(match))
            except ValueError:
                continue

        return numbers
