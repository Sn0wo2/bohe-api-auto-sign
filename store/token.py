import json
import os

from utils.paths import DATA_DIR

TOKEN_FILE = os.path.join(DATA_DIR, "token.json")

_TOKEN_KEYS = ("bohe_sign_token", "linux_do_connect_token", "linux_do_token")


def load_tokens() -> dict[str, str]:
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    init_tokens = {k: "" for k in _TOKEN_KEYS}

    if not any(os.getenv(k.upper()) for k in _TOKEN_KEYS):
        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(init_tokens, f, indent=4, ensure_ascii=False)

    return init_tokens


def save_tokens(**tokens: str) -> None:
    current = load_tokens()
    current.update({k: v for k, v in tokens.items() if v})
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=4, ensure_ascii=False)


def get_token(key: str) -> str | None:
    return load_tokens().get(key)
