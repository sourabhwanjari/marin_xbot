from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class SupportedLanguage(str, Enum):
    ENGLISH = "en"
    HINDI = "hi"
    MARATHI = "mr"
    GUJARATI = "gu"
    BENGALI = "bn"
    TAMIL = "ta"
    TELUGU = "te"
    KANNADA = "kn"
    MALAYALAM = "ml"

class LanguageDetectionResult(BaseModel):
    """Normalized output from the language detection engine."""
    language: str = Field("en", description="ISO 639-1 language code (e.g. en, hi, mr)")
    language_name: str = Field("English", description="Full localized or English name of the language")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Detection confidence score")
    script: str = Field("Latin", description="Detected script family (Latin, Devanagari, Dravidian, etc.)")
    is_supported: bool = Field(True, description="Whether full response generation is supported")
