import joblib
import re
from functools import lru_cache

from backend.api_config import (
    LABEL_FIELD,
    MODEL_PATH,
    SAFE_LABEL,
    TOXICITY_SCORE_FIELD,
    UNSAFE_LABEL,
    UNSAFE_KEYWORDS,
    UNSAFE_THRESHOLD,
    VECTORIZER_PATH,
)
from backend.text_processing import preprocess_text

MODEL = joblib.load(MODEL_PATH)
VECTORIZER = joblib.load(VECTORIZER_PATH)

# Precompile the regular expression for the fast-path keyword filter
KEYWORD_PATTERN = r'\b(?:' + '|'.join(map(re.escape, UNSAFE_KEYWORDS)) + r')\b'
KEYWORD_REGEX = re.compile(KEYWORD_PATTERN, re.IGNORECASE)


def _evaluate_text(cleaned_text: str) -> dict:
    """Internal function to evaluate safety, without caching or normalization."""
    # Fast path: Check rule-based keywords first
    if KEYWORD_REGEX.search(cleaned_text):
        return {
            TOXICITY_SCORE_FIELD: 1.0,
            LABEL_FIELD: UNSAFE_LABEL,
        }

    # Fallback path: ML Model Inference
    text_features = VECTORIZER.transform([cleaned_text])
    toxicity_score = float(MODEL.predict_proba(text_features)[0][1])
    label = UNSAFE_LABEL if toxicity_score >= UNSAFE_THRESHOLD else SAFE_LABEL

    return {
        TOXICITY_SCORE_FIELD: toxicity_score,
        LABEL_FIELD: label,
    }


@lru_cache(maxsize=10000)
def _evaluate_text_cached(cleaned_text: str) -> dict:
    """Cached wrapper around the internal evaluation function."""
    return _evaluate_text(cleaned_text)


def score_text_safety(text: str) -> dict:
    """Main entry point. Normalizes text and manages cache routing."""
    cleaned_text = preprocess_text(text)
    
    # Avoid caching tiny strings to save memory
    if not cleaned_text or len(cleaned_text) < 3:
        return _evaluate_text(cleaned_text)

    # Route normal queries through the cache wrapper
    return _evaluate_text_cached(cleaned_text)
