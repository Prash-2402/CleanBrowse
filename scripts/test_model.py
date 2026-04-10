from backend.api_config import SAFE_LABEL, UNSAFE_LABEL, UNSAFE_THRESHOLD
from backend.text_processing import preprocess_text
from backend.text_safety import MODEL, VECTORIZER


def predict(text):
    cleaned_text = preprocess_text(text)
    text_vec = VECTORIZER.transform([cleaned_text])
    prob = MODEL.predict_proba(text_vec)[0][1]
    label = UNSAFE_LABEL if prob >= UNSAFE_THRESHOLD else SAFE_LABEL
    print(f"Text: {text}")
    print(f"Prediction: {label}, Confidence: {prob:.2f}")
    print("-" * 40)


def main() -> None:
    predict("hello how are you")
    predict("this is explicit adult content")
    predict("I will kill you")


if __name__ == "__main__":
    main()
