import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
MODELS_DIR = PROJECT_ROOT / "models"
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DIR = PROJECT_ROOT / "docs"
EXTENSION_DIR = PROJECT_ROOT / "extension"

API_HOST = os.getenv("CLEANBROWSE_API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("CLEANBROWSE_API_PORT", "5000"))
API_DEBUG = os.getenv("CLEANBROWSE_API_DEBUG", "false").lower() == "true"

MODEL_PATH = Path(
    os.getenv("CLEANBROWSE_MODEL_PATH", str(MODELS_DIR / "model.pkl"))
)
VECTORIZER_PATH = Path(
    os.getenv("CLEANBROWSE_VECTORIZER_PATH", str(MODELS_DIR / "vectorizer.pkl"))
)
TRAINING_DATA_PATH = Path(
    os.getenv("CLEANBROWSE_TRAINING_DATA_PATH", str(DATA_DIR / "train.csv"))
)

ROOT_ROUTE = "/"
ANALYZE_TEXT_ROUTE = "/analyze-text"

TEXT_FIELD = "text"
TOXICITY_SCORE_FIELD = "toxicity_score"
LABEL_FIELD = "label"

SAFE_LABEL = "safe"
UNSAFE_LABEL = "unsafe"
UNSAFE_THRESHOLD = 0.5

HOME_MESSAGE = "Toxicity API is running."
HOME_EXAMPLE_TEXT = "You are amazing"
