import re
from typing import Dict, List, Set, Tuple

LANGUAGE_NAMES: Dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "gu": "Gujarati",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "or": "Odia"
}

# Distinctive Unicode Script Ranges
SCRIPT_RANGES: List[Tuple[str, str, str]] = [
    ("Tamil", "ta", r"[\u0B80-\u0BFF]"),
    ("Telugu", "te", r"[\u0C00-\u0C7F]"),
    ("Kannada", "kn", r"[\u0C80-\u0CFF]"),
    ("Malayalam", "ml", r"[\u0D00-\u0D7F]"),
    ("Gujarati", "gu", r"[\u0A80-\u0AFF]"),
    ("Bengali", "bn", r"[\u0980-\u09FF]"),
    ("Gurmukhi", "pa", r"[\u0A00-\u0A7F]"),
    ("Oriya", "or", r"[\u0B00-\u0B7F]"),
    ("Devanagari", "devanagari", r"[\u0900-\u097F]"),
    ("Latin", "en", r"[a-zA-Z]"),
]

# Marathi Unique Markers
# Note: The character 'ळ' (\u0933) is exclusively used in Marathi (and Sanskrit Vedic) among Devanagari languages in India, never in Modern Standard Hindi.
MARATHI_SPECIFIC_CHARACTERS = {"ळ"}

MARATHI_EXCLUSIVE_WORDS: Set[str] = {
    # Auxiliaries & Copulas
    "आहे", "आहेत", "नाही", "नाहीत", "होता", "होती", "होते", "होत्या", "असून", "असावी", "असेल",
    # Question words
    "काय", "कसा", "कशी", "कसे", "कुठे", "केव्हा", "कधी", "किती", "का",
    # Pronouns & determiners
    "मी", "आम्ही", "तू", "तुम्ही", "तो", "ती", "ते", "त्या", "आपण", "माझा", "माझी", "माझे", "तुझा", "तुझी", "तुझे", "तुमचा", "तुमची", "तुमचे", "त्यांचा", "त्यांची", "त्यांचे",
    # Postpositions & common markers
    "मध्ये", "साठी", "जवळ", "कडून", "वरून", "खाली", "आत", "बाहेर",
    # Marine & Direction vocabulary
    "समुद्र", "समुद्राची", "समुद्रात", "वारा", "वाऱ्याचा", "वाऱ्याची", "लाटा", "लाटांची", "मासेमारी", "मासे", "मासेमारीसाठी", "किनारा", "किनाऱ्यावर", "हवामान", "मार्ग", "रस्ता", "सुरक्षित", "छोटा",
    # Verbs / Instructions
    "दाखवा", "सांगा", "द्या", "करा", "जावे", "शकेल", "आहे", "बघा", "पहा", "शोधून"
}

# Marathi Suffix Patterns
MARATHI_SUFFIX_PATTERNS = [
    r"हून$",        # e.g., मुंबईहून
    r"जवळ$",       # e.g., मुंबईजवळ
    r"साठी$",       # e.g., मासेमारीसाठी
    r"मध्ये$",      # e.g., समुद्रात / समुद्रातमध्ये
    r"च्या$", r"ची$", r"चे$", r"ना$", r"ला$"
]

# Hindi Exclusive Words
HINDI_EXCLUSIVE_WORDS: Set[str] = {
    # Auxiliaries & Copulas
    "है", "हैं", "था", "थी", "थे", "होगा", "होगी", "होंगे", "नहीं", "मत", "रहा", "रही", "रहे", "सकता", "सकती", "सकते",
    # Question words
    "क्या", "कैसे", "कैसी", "कहाँ", "किधर", "कब", "कितना", "कितने", "कितनी", "क्यों", "कौन",
    # Pronouns & determiners
    "मैं", "हम", "तुम", "आप", "वह", "वे", "यह", "ये", "मेरा", "मेरी", "मेरे", "हमारा", "हमारी", "हमारे", "तुम्हारा", "तुम्हारी", "तुम्हारे", "उनका", "उनकी", "उनके", "इसका", "इसकी", "इसके",
    # Postpositions
    "का", "की", "के", "में", "से", "को", "पर", "लिए", "पास",
    # Marine & Direction vocabulary
    "रास्ता", "मौसम", "लहरें", "लहरों", "मछली", "मछुआरे", "हवा", "तूफान", "चक्रवात", "बताओ", "दिखाओ", "दीजिए", "कीजिए", "बताएं", "दिखाइए", "सुरक्षित", "छोटा", "क्षेत्र", "मत्स्य"
}
