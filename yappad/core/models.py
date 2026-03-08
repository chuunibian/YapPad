from dataclasses import dataclass
from pathlib import Path
from .constants import DEFAULT_WHISPER_MODEL, DEFAULT_COMPUTE_TYPE, DEFAULT_DEVICE

_DEFAULT_DIR = str(Path.home() / "Documents" / "YapPad") # this defaults to installation folder but not sure if that iswant is wanted

class MarkdownCommitNode:
    def __init__(self):
        self.markdown = ""
        self.id = 123
        self.tag = 1
 
@dataclass
class AppConfig:
    """Schema for app has defaults"""
    document_dir: str = _DEFAULT_DIR
    default_layout: int = 1
    default_whisper_model: str = DEFAULT_WHISPER_MODEL

@dataclass
class WhisperModelConfig:
    model_size_or_path: str = DEFAULT_WHISPER_MODEL
    device: str = DEFAULT_DEVICE
    compute_type: str = DEFAULT_COMPUTE_TYPE
