from platformdirs import user_data_dir
from pathlib import Path
from dataclasses import asdict
import json
from .models import AppConfig

APP_NAME = "YapPad"

# the appdata path
_CONFIG_PATH = Path(user_data_dir(APP_NAME, appauthor=False)) / "config.json"


def load_config() -> AppConfig:
    """Load config from disk, falling back to defaults if missing or invalid."""
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    appconfig = AppConfig()  # init with defaults

    try:
        data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        _CONFIG_PATH.write_text(json.dumps(asdict(appconfig), indent=2), encoding="utf-8")
        return appconfig

    if not isinstance(data, dict):
        _CONFIG_PATH.write_text(json.dumps(asdict(appconfig), indent=2), encoding="utf-8")
        return appconfig

    # load custom values, ignore unknown fields
    for k, v in data.items():
        if hasattr(appconfig, k):
            setattr(appconfig, k, v)

    return appconfig


def save_config(appconfig: AppConfig) -> None:
    """
    Get a config object
    the caller will create a new one and pass it in
    ideally caller will just query the setting comps and get the data
    """
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CONFIG_PATH.write_text(json.dumps(asdict(appconfig), indent=2), encoding="utf-8")
