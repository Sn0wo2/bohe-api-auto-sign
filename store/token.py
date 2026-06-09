import json
import os

from utils.paths import DATA_DIR

TOKEN_FILE = os.path.join(DATA_DIR, "token.json")

TokenValue = str

_TOKEN_KEYS = (
    "bohe_session_cookies",
    "linux_do_connect_token",
    "linux_do_token",
)

def _empty_tokens() -> dict[str, TokenValue]:
    return {key: "" for key in _TOKEN_KEYS}

def load_tokens() -> dict[str, TokenValue]:
    tokens = _empty_tokens()
    file_exists = os.path.exists(TOKEN_FILE)

    if file_exists:
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                raw_tokens = json.load(f)
        except (json.JSONDecodeError, OSError):
            raw_tokens = {}

        if isinstance(raw_tokens, dict):
            for key in _TOKEN_KEYS:
                value = raw_tokens.get(key)
                if isinstance(value, str) and value:
                    tokens[key] = value

    # Env overrides
    env_session_cookies = os.getenv("BOHE_SESSION_COOKIES")
    if env_session_cookies:
        tokens["bohe_session_cookies"] = env_session_cookies

    for key in _TOKEN_KEYS:
        if key == "bohe_session_cookies":
            continue
        env_value = os.getenv(key.upper())
        if env_value:
            tokens[key] = env_value

    if not file_exists and not any(tokens.values()):
        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(tokens, f, indent=4, ensure_ascii=False)

    return tokens


def save_tokens(**tokens: TokenValue | None) -> None:
    current = load_tokens()
    current.update({k: v for k, v in tokens.items() if k in _TOKEN_KEYS and v is not None})
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=4, ensure_ascii=False)
