import argparse

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from backend.api_config import MODEL_PATH, TRAINING_DATA_PATH, VECTORIZER_PATH
from backend.text_processing import preprocess_text

TOXIC_COLUMNS = [
    "toxic",
    "severe_toxic",
    "obscene",
    "threat",
    "insult",
    "identity_hate",
]


def load_dataset(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    required_columns = {"comment_text", *TOXIC_COLUMNS}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {missing}")

    df = df[["comment_text", *TOXIC_COLUMNS]].copy()
    df["label"] = (df[TOXIC_COLUMNS].fillna(0).sum(axis=1) > 0).astype(int)
    df = df[["comment_text", "label"]]
    df["comment_text"] = df["comment_text"].fillna("").apply(preprocess_text)
    df = df.dropna(subset=["label"])

    if df.empty:
        raise ValueError("Dataset is empty after preprocessing.")

    return df


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train a toxic comment classifier from the Kaggle toxic comment dataset."
    )
    parser.add_argument(
        "csv_path",
        nargs="?",
        default=str(TRAINING_DATA_PATH),
        help=f'Path to the Kaggle training CSV. Default: "{TRAINING_DATA_PATH}"',
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Fraction of data to reserve for testing. Default: 0.2",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducibility. Default: 42",
    )
    args = parser.parse_args()

    df = load_dataset(args.csv_path)

    X = df["comment_text"]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=y,
    )

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=5000,
        ngram_range=(1, 2),
        dtype=np.float32,
        sublinear_tf=True,
    )
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    model = LogisticRegression(max_iter=500, solver="liblinear")
    model.fit(X_train_tfidf, y_train)

    y_pred = model.predict(X_test_tfidf)

    average = "binary" if len(np.unique(y)) == 2 else "weighted"
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average=average, zero_division=0)
    recall = recall_score(y_test, y_pred, average=average, zero_division=0)

    print(f"Accuracy: {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    print(f"Saved model to {MODEL_PATH}")
    print(f"Saved vectorizer to {VECTORIZER_PATH}")


if __name__ == "__main__":
    main()
