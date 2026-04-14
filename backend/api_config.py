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
DATABASE_PATH = Path(
    os.getenv("CLEANBROWSE_DATABASE_PATH", str(BACKEND_DIR / "cleanbrowse.db"))
)

ROOT_ROUTE = "/"
ANALYZE_TEXT_ROUTE = "/analyze-text"
REPORT_EVENT_ROUTE = "/report-event"
REPORT_UNINSTALL_ROUTE = "/report-uninstall"
HEARTBEAT_ROUTE = "/heartbeat"
ANALYZE_IMAGE_ROUTE = "/analyze-image"
REPORT_STATUS_ROUTE = "/report-status"
DASHBOARD_ROUTE = "/dashboard"

# Time in seconds before we consider the heartbeat "lost"
# Alarm-based heartbeats fire every 30s (minimum for unpacked extensions),
# so we use 70s (2x interval + buffer) to avoid false positives.
HEARTBEAT_TIMEOUT = 70

# Max time drift in seconds before we suspect system sleep
SLEEP_DRIFT_THRESHOLD = 15 

# Browser processes to check before alerting "Protection Disabled"
MONITORED_BROWSERS = [
    "chrome.exe", 
    "msedge.exe", 
    "brave.exe", 
    "opera.exe", 
    "firefox.exe", 
    "vivaldi.exe", 
    "iexplore.exe", 
    "tor.exe"
]

IMAGE_MODEL_FILENAME = "nsfw_model.onnx"
IMAGE_MODEL_PATH = MODELS_DIR / IMAGE_MODEL_FILENAME

TEXT_FIELD = "text"
TOXICITY_SCORE_FIELD = "toxicity_score"
LABEL_FIELD = "label"

SAFE_LABEL = "safe"
UNSAFE_LABEL = "unsafe"
UNSAFE_THRESHOLD = 0.5

HOME_MESSAGE = "Toxicity API is running."
HOME_EXAMPLE_TEXT = "You are amazing"

UNSAFE_KEYWORDS = [
    "sex", "sexual", "erection", "erectile", "penile", "dysfunction", "pornographic", "explicit content", "adult video", 
    "adult site", "adult streaming", "adult subscription", "erotic video", 
    "sex tape", "leaked video", "private video", "hidden cam", 
    "sexvideo live", "sexvideo call", "sexvideo site", "sexvideo app", 
    "sexvideo chat", "sexvideo room", "sexvideo live stream", "blowjob", 
    "handjob", "gangbang", "threesome", "testes", "nude", "nudity", 
    "porn", "xxx", "nsfw", "escort", "escort service", "call girl", 
    "brothel", "massage parlor", "paid sex", "sex service", "fetish", 
    "bdsm", "domination", "submissive", "erotic", "seduction", "making out", 
    "foreplay", "climax", "orgasm", "penetration", "moaning", "arousal", 
    "seducing", "striptease", "lap dance", "dirty talk", "intimate", 
    "lust", "pleasure", "hookup", "one night stand", "sugar daddy", 
    "sugar baby", "lewd", "thirst trap", "spicy content", "fanhouse", 
    "fansly", "patreon adult", "private snaps", "premium snaps", "sexting", 
    "dirty chat", "roleplay sex", "boobs", "tits", "ass", "booty", 
    "pussy", "dick", "penis", "vagina", "breasts", "nipples", "genital", 
    "cleavage", "violence", "violent", "gore", "gore video", "bloodshed", 
    "blood scene", "abuse", "murder", "murder video", "kill", "killing", 
    "suicide methods", "suicide tips", "self harm", "cutting", 
    "how to die", "kill someone", "violent video", "torture", "execution", 
    "gambling", "casino", "casino app", "gambling site", "online casino", 
    "betting", "sportsbook", "betting tips", "betting app", "online betting", 
    "betting odds", "odds", "wager", "wager money", "parlay", "spread betting", 
    "live betting", "crypto betting", "fantasy betting", "real money games", 
    "cash games", "rummy cash", "teen patti cash", "lottery", "scratch cards", 
    "poker", "roulette", "slots", "drugs", "drugs online", "buy drugs", 
    "narcotics", "weed", "smoking", "cigarettes", "hookah", "alcohol", 
    "alcohol drink", "beer", "testicle", "testicles", "liquor", "drunk", 
    "vodka", "whiskey", "vaping", "vape", "vape pen", "ecigarette", 
    "cocaine", "meth", "heroin", "mdma", "lsd", "ecstasy", "pr0n", 
    "p0rn", "s3x", "fxck", "fuk", "fck", "seggs", "sx", "pron", 
    "po rn", "p orn", "sperm", "cum", "ejaculate", "orgy", "anal", 
    "vaginal", "fuck"
]
