from flask import Flask, jsonify, request

from backend.api_config import (
    ANALYZE_TEXT_ROUTE,
    API_DEBUG,
    API_HOST,
    API_PORT,
    HOME_EXAMPLE_TEXT,
    HOME_MESSAGE,
    ROOT_ROUTE,
    TEXT_FIELD,
)
from backend.text_safety import score_text_safety

app = Flask(__name__)


@app.get(ROOT_ROUTE)
def home():
    return jsonify(
        {
            "message": HOME_MESSAGE,
            "endpoint": ANALYZE_TEXT_ROUTE,
            "method": "POST",
            "example_request": {TEXT_FIELD: HOME_EXAMPLE_TEXT},
        }
    )


@app.post(ANALYZE_TEXT_ROUTE)
def analyze_text():
    data = request.get_json(silent=True)
    if not data or TEXT_FIELD not in data:
        return jsonify({"error": f'Request body must include "{TEXT_FIELD}".'}), 400

    return jsonify(score_text_safety(data[TEXT_FIELD]))


def main() -> None:
    app.run(host=API_HOST, port=API_PORT, debug=API_DEBUG)


if __name__ == "__main__":
    main()
