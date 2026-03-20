from .screens.main_screen import FullScreen
from .screens.editor_screen import EditorScreen
from .screens.mic_screen import MicScreen
from .screens.loopback_screen import LoopbackScreen
from .core.storage import load_config
from .core.constants import DEFAULT_MIC_SAMPLE_RATE, DEFAULT_LOOPBACK_SAMPLE_RATE
from .engine.sd_engine import sdEngine
from .engine.sd_consumer import SDParam
from .engine.loopback_engine import LoopbackEngine
from .engine.loopback_consumer import PyAWParam
from .engine.whisper_engine import TranscriptionEngine
from .widgets.loadingOverlay import LoadingOverlay

from textual.app import App
from textual.command import Provider, Hit
from textual.theme import Theme
from textual import work
from textual.worker import get_current_worker

from pathlib import Path
import queue


class ModeSwitchProvider(Provider):
    """Injects mode-switching commands into the Command Palette."""

    async def search(self, query: str):
        matcher = self.matcher(query)

        targets = [
            ("editor", "Switch to Editor"),
            ("mic", "Switch to Mic Mode"),
            ("loopback", "Switch to Loopback Mode"),
            ("full", "Switch to Full Mode"),
        ]

        for mode, description in targets:
            score = matcher.match(description)
            yield Hit(
                score=score if score > 0 else 0.1,
                match_display=matcher.highlight(description)
                if score > 0
                else description,
                command=lambda m=mode: self.app.switch_mode(m),
                help=f"Change layout to {mode}",
            )


class YapPad(App):
    """
    The app obj is the root comp
    basically acts as the global singleton containing stuff each screen needs
    """

    MODES = {
        "editor": EditorScreen,
        "mic": MicScreen,
        "loopback": LoopbackScreen,
        "full": FullScreen,
    }

    COMMANDS = App.COMMANDS | {ModeSwitchProvider}

    def __init__(self, args):
        super().__init__()
        self.args = args  # cli args when cli run app

    def on_mount(self) -> None:

        # Load config and ensure documents directory exists
        self.config = load_config()
        Path(self.config.document_dir).mkdir(parents=True, exist_ok=True)

        # Shared resources accessible from all screens using self.app
        self.is_recording = False
        self.is_loopback_recording = False

        self.audio_queue_mic = queue.Queue()
        self.audio_queue_loopback = queue.Queue()
        self.transcript_queue_mic = []
        self.transcript_queue_loopback = []

        self.mic_engine = sdEngine(
            SDParam(sample_rate=DEFAULT_MIC_SAMPLE_RATE, channels=1, dtype="float32")
        )
        self.loopback_engine = LoopbackEngine(
            PyAWParam(sample_rate=DEFAULT_LOOPBACK_SAMPLE_RATE, channels=1)
        )

        # TODO change this to something more robust later!
        if not self.args.slim:
            self.transcript_engine = TranscriptionEngine()

        # start transcription workers at app level
        self.transcription_loop_mic()
        self.transcription_loop_loopback()

        default_theme = Theme(
            name="default",
            primary="#C45AFF",
            secondary="#a684e8",
            warning="#FFD700",
            error="#FF4500",
            success="#00FA9A",
            accent="#FF69B4",
            background="#0F0F1F",
            surface="#1E1E3F",
            panel="#2D2B55",
            dark=True,
            variables={
                "footer-background": "transparent",
            },
        )

        self.register_theme(default_theme)
        self.theme = "default"

        self.switch_mode("editor")

    # --------------------------------------- Transcription Workers -------------------------------------------------

    @work(thread=True)
    def transcription_loop_mic(self):
        worker = get_current_worker()
        while not worker.is_cancelled:
            try:
                clip = self.audio_queue_mic.get(timeout=3)
                result, info = self.transcript_engine.transcribe(clip)
                text = " ".join(segment.text for segment in result)
                self.call_from_thread(self._dispatch_mic_transcript, text)
            except queue.Empty:
                continue

    @work(thread=True)
    def transcription_loop_loopback(self):
        worker = get_current_worker()
        while not worker.is_cancelled:
            try:
                clip = self.audio_queue_loopback.get(timeout=3)
                result, info = self.transcript_engine.transcribe(clip)
                text = " ".join(segment.text for segment in result)
                self.call_from_thread(self._dispatch_loopback_transcript, text)
            except queue.Empty:
                continue

    # so before transcription worker loop would append to a queue.Queue in which then the main UI thread needs to do wonky stuff on but it is not flexible
    # before transcription loop pushed to a thread safe queue.Queue which is an object from self (can only do this bc it is queue.Queue if it was [] then it is race cond)
    # now the transcription loop will just get the data and then call from thread to call a callback and that callback will RUN ON THE UI Thread but if we keep the footprint of this callback fun low then it should not block
    # it will just get the trans str and append it to a local queue (not thread safe one)
    # workflow is like | transcription_loop detects new | -> | calls callback | -> | callback checks if transcript has somethign there rn | -> | | -> | |
    # so then the event manager that handles the transfer transcript to user input will copy and paste and then blank out the transcript and then if queue len > 1 then pop and use else leave it blank

    # need dispatch checker since not every screen has the callback function for respective recorder
    def _dispatch_mic_transcript(self, text: str):
        """Route mic transcription to the active screen if it supports it."""
        screen = self.screen
        if hasattr(screen, "append_transcript_mic"):
            screen.append_transcript_mic(text)

    def _dispatch_loopback_transcript(self, text: str):
        """Route loopback transcription to the active screen if it supports it."""
        screen = self.screen
        if hasattr(screen, "append_transcript_loopback"):
            screen.append_transcript_loopback(text)

    # --------------------------------------- Whisper Model Switch Worker -------------------------------------------------

    @work(thread=True)
    def switch_whisper_model(self, config):
        """Worker thread that switches the whisper model and dismisses the loading overlay via call_from_thread.
        
           For this the callback is a function that mutates the UI but in this case it is safe to mutate the UI in the callback
           since the callback just pushes a task to main thread runtime to be done
        
        """
        worker = get_current_worker()
        try:
            self.transcript_engine.switch_model(config)
            if not worker.is_cancelled:
                self.call_from_thread(self._on_model_switch_success, config.model_size_or_path)
        except Exception as e:
            if not worker.is_cancelled:
                self.call_from_thread(self._on_model_switch_error, str(e))

    def _on_model_switch_success(self, model_name: str) -> None:
        """Called on UI thread after model switch succeeds."""
        # Dismiss the loading overlay (it's the top screen on the stack)
        if isinstance(self.screen, LoadingOverlay):
            self.screen.dismiss(None)

    def _on_model_switch_error(self, error_msg: str) -> None:
        """Called on UI thread after model switch fails."""
        if isinstance(self.screen, LoadingOverlay):
            self.screen.dismiss(None)
        self.notify(f"Model switch failed: {error_msg}", severity="error")
