from pathlib import Path
import sys

if sys.version_info >= (3, 11):
    import tomllib as tomli
else:
    import tomli  # type: ignore[no-redef]

import tomli_w

CONFIG_DIR = Path.home() / ".config" / "q"
CONFIG_PATH = CONFIG_DIR / "config.toml"

DEFAULTS = {
    "server": {
        "base_url": "http://localhost:1234/v1",
        "model": "",
        "api_key": "",
    },
    "prompt": {
        "system": (
            "You are a concise, professional Linux and programming assistant. "
            "Answer questions directly and practically. Prefer concrete commands "
            "and code examples over explanations. Keep responses brief and focused."
        ),
    },
}


def load(path=None):
    path = path or CONFIG_PATH
    merged = {}
    for section, values in DEFAULTS.items():
        merged[section] = dict(values)
    if path.exists():
        with open(path, "rb") as f:
            data = tomli.load(f)
        for section, values in data.items():
            if section in merged:
                merged[section].update(values)
            else:
                merged[section] = values
    return merged


def save(cfg, path=None):
    path = path or CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        tomli_w.dump(cfg, f)
