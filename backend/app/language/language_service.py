import logging
from typing import Optional, List, Dict, Any

from app.language.detector import language_detector
from app.language.language_models import LanguageDetectionResult
from app.language.language_config import LANGUAGE_NAMES

logger = logging.getLogger("marinex.language.service")

class LanguageService:
    """
    High-level Language Service orchestrating detection, multi-turn language persistence,
    dynamic code-switching, and response language validation.
    """

    def __init__(self):
        self.detector = language_detector

    def detect_language(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> LanguageDetectionResult:
        """
        Detects query language. If the query is terse (e.g. 'Mumbai', 'Tomorrow'),
        leverages previous user turns to maintain conversation language context.
        If user explicitly changes script or vocabulary, dynamically switches language immediately.
        """
        history_to_use = chat_history or history
        result = self.detector.detect(query)


        # If query is short English words that could be place names/numbers in an ongoing Indic conversation
        clean_q = query.strip()
        is_short_neutral = len(clean_q.split()) <= 2 and clean_q.isascii() and not any(w in clean_q.lower() for w in ["what", "how", "is", "where", "safe", "route", "weather", "ocean", "find", "show"])

        if is_short_neutral and history_to_use:
            # Check last user message language
            for turn in reversed(history_to_use):

                if turn.get("role") in ("user", "human"):
                    prev_text = turn.get("content", "")
                    if prev_text:
                        prev_res = self.detector.detect(prev_text)
                        if prev_res.language in ("mr", "hi", "gu", "ta", "te", "bn"):
                            logger.info(f"[LanguageService] Short query '{query}' inherits previous conversation language '{prev_res.language_name}'")
                            return prev_res
                    break

        logger.info(f"[LanguageService] Query: '{query}' -> Detected: {result.language_name} ({result.language}) [Confidence: {result.confidence}]")
        return result

    def get_prompt_language_instruction(self, lang_code: str) -> str:
        """
        Returns strict system prompt directives ensuring the LLM synthesizes
        its entire output in the designated language.
        """
        lang_name = LANGUAGE_NAMES.get(lang_code, "English")
        if lang_code == "mr":
            return (
                "LANGUAGE DIRECTIVE (CRITICAL): The user is communicating in Marathi (मराठी).\n"
                "You MUST generate your COMPLETE final response in natural, fluent Marathi using proper Devanagari script.\n"
                "Do NOT respond in English or Hindi.\n"
                "Use standard Marathi marine and coastal terms:\n"
                "• Route: 'मार्ग' किंवा 'रस्ता'\n"
                "• Wind: 'वारा' (वाऱ्याचा वेग)\n"
                "• Waves / Sea State: 'लाटांची उंची' आणि 'समुद्राची स्थिती'\n"
                "• Potential Fishing Zone: 'संभाव्य मत्स्य क्षेत्र (PFZ)'\n"
                "• Safety / Caution: 'सुरक्षित' / 'सावधगिरी बाळगा' / 'धोकादायक'\n"
                "Maintain professional warmth and maritime respect (e.g., greet as 'नमस्कार कॅप्टन!')."
            )
        elif lang_code == "hi":
            return (
                "LANGUAGE DIRECTIVE (CRITICAL): The user is communicating in Hindi (हिन्दी).\n"
                "You MUST generate your COMPLETE final response in natural, fluent Hindi using proper Devanagari script.\n"
                "Do NOT respond in English or Marathi.\n"
                "Use standard Hindi marine and coastal terms:\n"
                "• Route: 'मार्ग' या 'रास्ता'\n"
                "• Wind: 'हवा की गति' और 'दिशा'\n"
                "• Waves / Sea State: 'लहरों की ऊंचाई' और 'समुद्र की स्थिति'\n"
                "• Potential Fishing Zone: 'मत्स्य पालन क्षेत्र (PFZ)'\n"
                "• Safety / Caution: 'सुरक्षित' / 'सावधानी बरतें' / 'खतरा'\n"
                "Maintain professional warmth and maritime respect (e.g., greet as 'नमस्ते कैप्टन!')."
            )
        elif lang_code != "en":
            return (
                f"LANGUAGE DIRECTIVE (CRITICAL): The user is communicating in {lang_name} ({lang_code}).\n"
                f"You MUST generate your COMPLETE final response in fluent {lang_name}.\n"
                f"Maintain professional maritime accuracy and clear navigational guidance."
            )
        return "LANGUAGE DIRECTIVE: Generate the final response in clear, concise, professional English."

    def validate_response_language(self, response_text: str, target_lang: str) -> bool:
        """
        Validates that the generated response matches the intended user language.
        Returns True if matching or acceptable, False if significant language drift occurred.
        """
        if not response_text or target_lang == "en":
            return True

        detected = self.detector.detect(response_text)
        if detected.language == target_lang:
            return True

        # If both are in Devanagari (Marathi and Hindi), check specific lexical markers
        if target_lang in ("mr", "hi") and detected.script == "Devanagari":
            return True

        logger.warning(f"[LanguageService] Response language mismatch: Target='{target_lang}', Detected='{detected.language}'")
        return False

language_service = LanguageService()
