from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Select, Switch, Static, Input, Button

from ..core.storage import save_config
from ..core.constants import WHISPER_MODELS, AUDIO_SOURCES, DETECT_MODES
from pathlib import Path


'''

    Overall a basic verticle of comp setting components:

    A drop down for sounddevice selection (also make it so it defaults to something on startup with notificaiton)

    A dropdown for which whisper faster model to use for transcription

    Toggle or dropdown for autodetect(Auto detect silence and then queue) or manual trigger

    Dropdown for outside speaking to mic or from device audio or both (if both need separate threads and queues I htink)


'''


SOUNDDEVICES = [("Default Microphone", "default"), ("USB Headset", "usb"), ("Bluetooth", "bt")]  # TODO: replace with real device enumeration


class LocalSettings(Vertical):

    def compose(self) -> ComposeResult:
        yield Label("Settings", id="settings-title")

        # Documents directory setting
        yield Label("Documents Directory")
        yield Input(
            value=self.app.config.document_dir,
            placeholder="Path to documents folder",
            id="documents-dir-input",
        )
        yield Button("Apply", id="apply-docs-dir-btn", variant="primary")

        yield Select(SOUNDDEVICES, prompt="Sounddevice", id="sounddevice")
        yield Select(WHISPER_MODELS, prompt="Whisper Model", id="whisper-model")
        yield Select(AUDIO_SOURCES, prompt="Audio Source", id="audio-source")
        yield Select(DETECT_MODES, prompt="Detect Mode", id="detect-mode")
        with Vertical(id="toggle-row"):
            yield Label("Auto-queue on silence")
            yield Switch(value=False, id="auto-queue-toggle")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "apply-docs-dir-btn":
            dir_input = self.query_one("#documents-dir-input", Input)
            new_path = dir_input.value.strip()

            if not new_path:
                self.notify("Path cannot be empty", severity="error")
                return

            try:
                Path(new_path).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.notify(f"Invalid path: {e}", severity="error")
                return

            self.app.config.document_dir = new_path
            save_config(self.app.config)
            self.notify(f"Documents directory set to: {new_path}")
            self.notify("Previous files remain at their old location", severity="information")