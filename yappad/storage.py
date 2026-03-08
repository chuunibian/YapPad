from platformdirs import user_data_dir
from pathlib import Path
import json

APP_NAME = "YapPad"

# the appdata path and the default path can just leave it like this for now
_CONFIG_PATH = Path(user_data_dir(APP_NAME, appauthor=False)) / "config.json"
_DEFAULT_DIR = str(Path.home() / "Documents" / "YapPad")

# config singleton obj from the loaded config
# tbh in the future might be better to just make it in its own singleotn file
_config: dict | None = None


def _load() -> dict:
    """Read config.json, or create it with defaults. Returns the config dict."""
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "documents_dir" in data:
            return data
    except Exception:
        pass
    # Missing, corrupted, or invalid — reset to defaults
    defaults = {"documents_dir": _DEFAULT_DIR}
    _CONFIG_PATH.write_text(json.dumps(defaults, indent=2), encoding="utf-8")
    return defaults


def get_documents_dir() -> Path:
    """Return the current documents directory, creating it if needed."""
    global _config
    if _config is None:
        _config = _load()
    p = Path(_config["documents_dir"])
    p.mkdir(parents=True, exist_ok=True)
    return p


def set_documents_dir(new_path: str) -> tuple[bool, str | None]:
    """Validate, persist, and update the documents directory. Does NOT move files."""
    global _config
    if _config is None:
        _config = _load()
    try:
        Path(new_path).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return (False, f"Invalid path: {e}")
    _config["documents_dir"] = str(Path(new_path))
    _CONFIG_PATH.write_text(json.dumps(_config, indent=2), encoding="utf-8")
    return (True, None)


def load_config():
    pass
