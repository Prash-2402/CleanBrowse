import joblib

from backend.api_config import (
    LABEL_FIELD,
    MODEL_PATH,
    SAFE_LABEL,
    TOXICITY_SCORE_FIELD,
    UNSAFE_LABEL,
    UNSAFE_THRESHOLD,
    VECTORIZER_PATH,
)
from backend.text_processing import preprocess_text

MODEL = joblib.load(MODEL_PATH)
VECTORIZER = joblib.load(VECTORIZER_PATH)


def score_text_safety(text: str) -> dict:
    cleaned_text = preprocess_text(text)
    text_features = VECTORIZER.transform([cleaned_text])
    toxicity_score = float(MODEL.predict_proba(text_features)[0][1])
    label = UNSAFE_LABEL if toxicity_score >= UNSAFE_THRESHOLD else SAFE_LABEL

    return {
        TOXICITY_SCORE_FIELD: toxicity_score,
        LABEL_FIELD: label,
    }
