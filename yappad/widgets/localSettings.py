from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Select, Switch, Input, Button
from textual import on

from ..core.storage import save_config
from ..core.constants import WHISPER_MODELS, DEVICES
from ..engine.whisper_engine import TranscriptionEngine
from pathlib import Path

from ..core.models import WhisperModelConfig
from .loadingOverlay import LoadingOverlay


class LocalSettings(Vertical):
    def _build_device_options(self, devices: list[dict]) -> list[tuple[str, str]]:
        """Convert engine get_devices() dicts into (label, value) tuples for Select."""
        return [(d["label"], d["name"]) for d in devices]

    def _build_model_options(self) -> list[tuple[str, str]]:
        """Build whisper model options, marking downloaded ones with ✓."""
        downloaded = TranscriptionEngine.get_downloaded_models()
        options = []
        for label, value in WHISPER_MODELS:
            if value in downloaded:
                options.append((f"{label}  ✅", value))
            else:
                options.append((label, value))
        return options

    def compose(self) -> ComposeResult:
        yield Label("Settings", id="settings-title")

        # ── Documents directory ──
        yield Label("📁 Documents Directory")
        yield Input(
            value=self.app.config.document_dir,
            placeholder="Path to documents folder",
            id="documents-dir-input",
        )
        yield Button("Apply Path", id="apply-docs-dir-btn", variant="primary")

        # ── Audio device selection ──
        yield Label("🎤 Audio Devices")
        mic_devices = self._build_device_options(self.app.mic_engine.get_devices())
        yield Select(mic_devices, prompt="Microphone", id="mic-device")

        loopback_devices = self._build_device_options(
            self.app.loopback_engine.get_devices()
        )
        yield Select(loopback_devices, prompt="Loopback Device", id="loopback-device")

        # ── Whisper settings ──
        yield Label("Whisper Model")
        with Vertical(id="whisper-settings-container"):
            yield Select(
                self._build_model_options(),
                prompt="Whisper Model",
                id="whisper-model",
                value=self.app.config.default_whisper_model,
            )
            yield Select(
                DEVICES,
                prompt="Whisper Device",
                id="whisper-device",
                value=self.app.config.default_device,
            )
            yield Button(
                "Apply Whisper", id="apply-whisper-btn", variant="primary"
            )

        # ── Misc ──
        with Vertical(id="toggle-row"):
            yield Label("Auto-queue on silence")
            yield Switch(value=False, id="auto-queue-toggle")

    # ── Device switching handlers ──

    @on(Select.Changed, "#mic-device")
    def on_mic_device_changed(self, event: Select.Changed) -> None:
        """
        When select it instantly tries to apply the change with no confirmation
        """
        if event.value is Select.BLANK:
            return
        if self.app.is_recording:
            self.notify(
                "Stop mic recording before switching devices", severity="warning"
            )
            return
        self.app.mic_engine.switch_device(event.value)
        self.notify(f"Mic device → {event.value}")

    @on(Select.Changed, "#loopback-device")
    def on_loopback_device_changed(self, event: Select.Changed) -> None:
        if event.value is Select.BLANK:
            return
        if self.app.is_loopback_recording:
            self.notify(
                "Stop loopback recording before switching devices", severity="warning"
            )
            return
        self.app.loopback_engine.switch_device(event.value)
        self.notify(f"Loopback device → {event.value}")

    # ── Other handlers ──

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
            self.notify(
                "Previous files remain at their old location", severity="information"
            )
        elif event.button.id == "apply-whisper-btn":
            model_select = self.query_one("#whisper-model", Select)
            device_select = self.query_one("#whisper-device", Select)

            if (
                model_select.value == Select.BLANK
                or device_select.value == Select.BLANK
            ):
                self.notify(
                    "Please select both a model and a device", severity="warning"
                )
                return

            # Save new config
            # TODO remove this later and add it into another place as this resaves the config each time
            self.app.config.default_whisper_model = model_select.value
            self.app.config.default_device = device_select.value
            save_config(self.app.config)

            # push loading modal and trigger worker
            # TODO compute type should be gotten from a dropdown rn doesnt have
            new_config = WhisperModelConfig(
                model_size_or_path=model_select.value, device=device_select.value, compute_type="cpu"
            )

            self.app.push_screen(LoadingOverlay(
                f"Loading {model_select.value} on {device_select.value}..."
            )) # push blocking loading screen

            self.app.switch_whisper_model(new_config)
