from pathlib import Path

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