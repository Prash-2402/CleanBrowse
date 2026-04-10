import re

NON_ALPHANUMERIC_PATTERN = re.compile(r"[^a-z0-9\s]")
WHITESPACE_PATTERN = re.compile(r"\s+")


def preprocess_text(text: str) -> str:
    normalized_text = str(text).lower()
    normalized_text = NON_ALPHANUMERIC_PATTERN.sub("", normalized_text)
    normalized_text = WHITESPACE_PATTERN.sub(" ", normalized_text).strip()
    return normalized_text
