from platformdirs import user_data_dir
from pathlib import Path

APP_NAME = "YapPad"


def get_data_dir() -> Path:
    """Return the cross-platform app data directory, creating it if needed."""
    p = Path(user_data_dir(APP_NAME, appauthor=False))
    p.mkdir(parents=True, exist_ok=True)
    return p
