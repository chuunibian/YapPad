from .screens.main_screen import FullScreen
from .screens.editor_screen import EditorScreen
from .screens.mic_screen import MicScreen
from .screens.loopback_screen import LoopbackScreen
from .storage import get_data_dir
from .sdconsumer import AudioCaptureT, SDParam
from .loopbackconsumer import DeviceLoopbackCaptureT, PyAWParam

from textual.app import App
from textual.command import Provider, Hit
from textual.theme import Theme
from textual import work
from textual.worker import get_current_worker

from faster_whisper import WhisperModel
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
                match_display=matcher.highlight(description) if score > 0 else description,
                command=lambda m=mode: self.app.switch_mode(m),
                help=f"Change layout to {mode}"
            )


class YapPad(App):

    '''
    The app obj is the root comp
    basically acts as the global singleton containing stuff each screen needs
    '''

    MODES = {
        "editor": EditorScreen,
        "mic": MicScreen,
        "loopback": LoopbackScreen,
        "full": FullScreen,
    }

    COMMANDS = App.COMMANDS | {ModeSwitchProvider}

    def on_mount(self) -> None:

        # Shared resources accessible from all screens using self.app
        self.is_recording = False
        self.is_loopback_recording = False

        self.audio_queue_mic = queue.Queue()
        self.audio_queue_loopback = queue.Queue()
        self.transcript_queue_mic = []
        self.transcript_queue_loopback = []

        self.recorder = AudioCaptureT(SDParam(sample_rate=16000, channels=1, dtype="float32"))
        self.loopback_recorder = DeviceLoopbackCaptureT(PyAWParam(sample_rate=48000, channels=1))

        self.transcript_model = WhisperModel("base", device="cpu", compute_type="int8")

        # start transcription workers at app level
        self.transcription_loop_mic()
        self.transcription_loop_loopback()

        # ensure app data directory exists on startup
        get_data_dir()

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
                result, info = self.transcript_model.transcribe(clip)
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
                result, info = self.transcript_model.transcribe(clip)
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
        if hasattr(screen, 'append_transcript_mic'):
            screen.append_transcript_mic(text)

    def _dispatch_loopback_transcript(self, text: str):
        """Route loopback transcription to the active screen if it supports it."""
        screen = self.screen
        if hasattr(screen, 'append_transcript_loopback'):
            screen.append_transcript_loopback(text)


def main():
    app = YapPad()
    app.run()

if __name__ == "__main__":
    main()
