from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Select, Switch, Static


'''

    Overall a basic verticle of comp setting components:

    A drop down for sounddevice selection (also make it so it defaults to something on startup with notificaiton)

    A dropdown for which whisper faster model to use for transcription

    Toggle or dropdown for autodetect(Auto detect silence and then queue) or manual trigger

    Dropdown for outside speaking to mic or from device audio or both (if both need separate threads and queues I htink)


'''


SOUNDDEVICES = [("Default Microphone", "default"), ("USB Headset", "usb"), ("Bluetooth", "bt")]
WHISPER_MODELS = [("Tiny", "tiny"), ("Base", "base"), ("Small", "small"), ("Medium", "medium")]
AUDIO_SOURCES = [("Microphone", "mic"), ("Device Audio", "device"), ("Both", "both")]
DETECT_MODES = [("Auto Detect", "auto"), ("Manual Trigger", "manual")]


class LocalSettings(Vertical):

    def compose(self) -> ComposeResult:
        yield Label("Settings", id="settings-title")
        yield Select(SOUNDDEVICES, prompt="Sounddevice", id="sounddevice")
        yield Select(WHISPER_MODELS, prompt="Whisper Model", id="whisper-model")
        yield Select(AUDIO_SOURCES, prompt="Audio Source", id="audio-source")
        yield Select(DETECT_MODES, prompt="Detect Mode", id="detect-mode")
        with Vertical(id="toggle-row"):
            yield Label("Auto-queue on silence")
            yield Switch(value=False, id="auto-queue-toggle")
    