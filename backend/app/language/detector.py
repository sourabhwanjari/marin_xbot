import re
import logging
from typing import Optional, Dict, Any

from app.language.language_models import LanguageDetectionResult, SupportedLanguage
from app.language.language_config import (
    LANGUAGE_NAMES,
    SCRIPT_RANGES,
    MARATHI_SPECIFIC_CHARACTERS,
    MARATHI_EXCLUSIVE_WORDS,
    MARATHI_SUFFIX_PATTERNS,
    HINDI_EXCLUSIVE_WORDS
)

logger = logging.getLogger("marinex.language.detector")

class LanguageDetector:
    """
    Automatic Language Detection Engine for MARINEX AI.
    Accurately and deterministically detects English, Hindi, Marathi, and other Indic scripts
    without external cloud API dependencies.
    """

    @classmethod
    def detect(cls, text: str) -> LanguageDetectionResult:
        """
        Detects the primary language of the input text.
        Returns LanguageDetectionResult with language code (en, hi, mr), full name, and confidence.
        """
        if not text or not text.strip():
            return LanguageDetectionResult(
                language="en",
                language_name="English",
                confidence=1.0,
                script="Latin",
                is_supported=True
            )

        cleaned_text = text.strip()

        # 1. Count characters across script categories
        script_counts: Dict[str, int] = {}
        for script_name, lang_code, pattern in SCRIPT_RANGES:
            matches = len(re.findall(pattern, cleaned_text))
            if matches > 0:
                script_counts[script_name] = matches

        if not script_counts:
            # Fallback to English if purely digits/punctuation
            return LanguageDetectionResult(
                language="en",
                language_name="English",
                confidence=0.8,
                script="Latin",
                is_supported=True
            )

        # Primary script with highest count
        dominant_script = max(script_counts.items(), key=lambda x: x[1])[0]

        # 2. Check non-Devanagari scripts directly
        for script_name, lang_code, _ in SCRIPT_RANGES:
            if dominant_script == script_name and script_name not in ("Devanagari", "Latin"):
                return LanguageDetectionResult(
                    language=lang_code,
                    language_name=LANGUAGE_NAMES.get(lang_code, script_name),
                    confidence=0.98,
                    script=dominant_script,
                    is_supported=True
                )

        # 3. Check Latin script (English)
        if dominant_script == "Latin":
            return LanguageDetectionResult(
                language="en",
                language_name="English",
                confidence=0.99,
                script="Latin",
                is_supported=True
            )

        # 4. Devanagari script: Disambiguate Marathi vs Hindi
        if dominant_script == "Devanagari":
            # Direct character check for 'ळ'
            for ch in MARATHI_SPECIFIC_CHARACTERS:
                if ch in cleaned_text:
                    logger.info(f"[LanguageDetector] Detected Marathi via unique character '{ch}' in: '{cleaned_text}'")
                    return LanguageDetectionResult(
                        language="mr",
                        language_name="Marathi",
                        confidence=0.99,
                        script="Devanagari",
                        is_supported=True
                    )

            # Tokenize words
            tokens = re.findall(r"[\u0900-\u097F]+", cleaned_text)
            marathi_score = 0.0
            hindi_score = 0.0

            for tok in tokens:
                # Direct word matches
                if tok in MARATHI_EXCLUSIVE_WORDS:
                    marathi_score += 2.0
                if tok in HINDI_EXCLUSIVE_WORDS:
                    hindi_score += 2.0

                # Marathi suffixes (e.g. -हून, -जवळ, -साठी)
                for pat in MARATHI_SUFFIX_PATTERNS:
                    if re.search(pat, tok):
                        marathi_score += 1.5
                        break

            logger.debug(f"[LanguageDetector] Devanagari scores for '{cleaned_text}': Marathi={marathi_score}, Hindi={hindi_score}")

            if marathi_score > hindi_score:
                conf = min(0.85 + (marathi_score * 0.03), 0.99)
                return LanguageDetectionResult(
                    language="mr",
                    language_name="Marathi",
                    confidence=round(conf, 2),
                    script="Devanagari",
                    is_supported=True
                )
            elif hindi_score > marathi_score:
                conf = min(0.85 + (hindi_score * 0.03), 0.99)
                return LanguageDetectionResult(
                    language="hi",
                    language_name="Hindi",
                    confidence=round(conf, 2),
                    script="Devanagari",
                    is_supported=True
                )
            else:
                # In tie situations, check specific prompt patterns
                # e.g., "मुंबईजवळ", "कशी आहे"
                if any(k in cleaned_text for k in ["जवळ", "आहे", "काय", "दाखवा", "सांगा", "मासेमारी"]):
                    return LanguageDetectionResult(
                        language="mr",
                        language_name="Marathi",
                        confidence=0.90,
                        script="Devanagari",
                        is_supported=True
                    )
                # Default Devanagari to Hindi if neutral
                return LanguageDetectionResult(
                    language="hi",
                    language_name="Hindi",
                    confidence=0.88,
                    script="Devanagari",
                    is_supported=True
                )

        return LanguageDetectionResult(
            language="en",
            language_name="English",
            confidence=0.90,
            script="Latin",
            is_supported=True
        )

language_detector = LanguageDetector()
