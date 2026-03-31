from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from .constants import DEFAULT_WHISPER_MODEL, DEFAULT_COMPUTE_TYPE, DEFAULT_DEVICE

_DEFAULT_DIR = str(
    Path.home() / "Documents" / "YapPad"
)  # this defaults to installation folder but not sure if that iswant is wanted


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
    default_device: str = DEFAULT_DEVICE
    last_opened_file: str = ""


@dataclass
class TranscriptionConfig:
    vad_flag = True
    # other stuff
    language = "en"


@dataclass
class WhisperModelConfig:
    """
    Params used to init a faster whisper model config
    """

    model_size_or_path: str = DEFAULT_WHISPER_MODEL
    device: str = DEFAULT_DEVICE
    compute_type: str = DEFAULT_COMPUTE_TYPE


def WhisperModelComputeTypeMapper(device):
    """
    For utility use
    sticking to just storing cuda or cpu and then mapping it
    """
    if device == "cuda":
        return "float16"
    else: # default
        return "int8"


@dataclass
class TranscriptClip:
    """One block of transcribed audio. Timestamp is auto-filled on creation."""

    text: str
    timestamp: str = field(
        default_factory=lambda: datetime.now().strftime("%H:%M:%S")
    )

