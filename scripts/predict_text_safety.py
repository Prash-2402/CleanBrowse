from backend.api_config import SAFE_LABEL, UNSAFE_LABEL, UNSAFE_THRESHOLD
from backend.text_processing import preprocess_text
from backend.text_safety import MODEL, VECTORIZER

UNSAFE_KEYWORDS = {
    "abuse",
    "attack",
    "bastard",
    "die",
    "harass",
    "hate",
    "idiot",
    "kill",
    "moron",
    "racist",
    "slur",
    "stupid",
    "threat",
    "trash",
    "violence",
}


def predict_text_safety(text: str) -> dict:
    cleaned_text = preprocess_text(text)

    # Fast rule-based shortcut for obviously unsafe text.
    for word in UNSAFE_KEYWORDS:
        if word in cleaned_text:
            return {
                "probability_score": 1.0,
                "predicted_label": "unsafe",
                "source": "keyword_match",
                "matched_keyword": word,
            }

    text_features = VECTORIZER.transform([cleaned_text])

    probability = float(MODEL.predict_proba(text_features)[0][1])
    predicted_label = UNSAFE_LABEL if probability >= UNSAFE_THRESHOLD else SAFE_LABEL

    return {
        "probability_score": probability,
        "predicted_label": predicted_label,
        "source": "ml_model",
        "matched_keyword": None,
    }
