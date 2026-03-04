from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, RichLog, TextArea, Label, Markdown
from textual.containers import Container, Horizontal, Vertical
from rich.markdown import Markdown
from textual import on, events, work
from textual.binding import Binding
from textual.screen import Screen
from textual.reactive import reactive

from faster_whisper import WhisperModel

from ..sdconsumer import AudioCaptureT, SDParam
from ..loopbackconsumer import DeviceLoopbackCaptureT, PyAWParam

from ..widgets.userInputArea import UserInputArea
from ..widgets.transcriptInputArea import TranscriptRichLog
from ..widgets.transcriptEditor import TranscriptEditor
from ..widgets.markdownArea import MasterMarkdown
from ..widgets.customTranscriptFooter import CustomTranscriptFooter
from ..widgets.topBar import TopBar
from ..widgets.popupComponent import PopupComponent

import queue
import numpy as np
from pathlib import Path
from textual.worker import Worker, get_current_worker


class MarkdownLogScreen(Screen):

    BINDINGS = [
        Binding("alt+s", "toggle_record", "record toggle", priority=True),
        Binding("alt+d", "toggle_loopback_record", "loopback toggle", priority=True),
        Binding("alt+m", "grab_mic_transcript", "grab mic", priority=True),
        Binding("alt+l", "grab_loopback_transcript", "grab loopback", priority=True),
        Binding("alt+y", "temp_commit", "commit", priority=True),
        Binding("ctrl+o", "open_popup", "Open"),
        Binding("ctrl+s", "save_file", "Save"),
    ]

    # reactive states
    current_file_path: reactive[str] = reactive("")
    is_saved: reactive[bool] = reactive(True)

    is_recording = False

    CSS_PATH = "../styles/temp2.tcss"

    MARKDOWN_CONTENT = "" # !! TEMP used for mvp mock markdown string

    # --------------------------------------- On X -------------------------------------------------

    # acts as the __init__ for instance vars
    def on_mount(self) -> None:

        self.is_recording = False
        self.is_loopback_recording = False

        # -- Separate queues for mic and loopback --
        self.audio_queue_mic = queue.Queue()
        self.audio_queue_loopback = queue.Queue()
        self.transcript_queue_mic = []
        self.transcript_queue_loopback = []

        # -- Audio Recording Wrapper Objects --
        self.recorder = AudioCaptureT(SDParam(sample_rate=16000, channels=1, dtype="float32"))
        self.loopback_recorder = DeviceLoopbackCaptureT(PyAWParam(sample_rate=48000, channels=1))

        # -- Whisper Model stuff --
        self.transcript_model = WhisperModel("base", device="cpu", compute_type="int8")
        self.transcription_loop_mic()
        self.transcription_loop_loopback()

        # set initial border titles
        self.query_one('#transcript', TextArea).border_title = "⚪ Mic Idle"
        self.query_one('#transcript-loopback', TextArea).border_title = "⚪ Loopback Idle"
    
    # making the parent comp of user input text area catch the mesage and do an action
    # this parent will get textar change from 2 places since there are 2 textareas unless use the css filter 
    @on(TextArea.Changed, '#user')
    def on_user_input_changed(self) -> None:
        user_input_widget = self.query_one("#user", TextArea)
        master_markdown_widget = self.query_one("#master", MasterMarkdown)

        # mark as unsaved when user edits
        # for now the detection of if it is edited or not is checked for each keystroke though perfoamcne wise no worry isnce it is 
        # bound to a reactive state but msot of the time is a no operation
        if self.current_file_path:
            self.is_saved = False

        # TODO have this logic for now it updates preview real time but this will not scale
        # master_markdown_widget.update(user_input_widget.text)

    
    # --------------------------------------- Actions -------------------------------------------------

    def action_temp_commit(self) -> None:
        user_input_widget = self.query_one("#user", TextArea)
        master_markdown_widget = self.query_one("#master", MasterMarkdown)

        if user_input_widget.text != "":
            master_markdown_widget.update(user_input_widget.text)
            user_input_widget.text = "" # clear it after commit
        else:
            self.notify("Nothing in user input area to append")


    def _grab_transcript(self, widget_id: str, editor_id: str, queue_list: list) -> None:
        """Generic grab logic for either mic or loopback transcript."""
        transcript_widget = self.query_one(f'#{widget_id}', TextArea)

        if len(queue_list) != 0:
            current_data = transcript_widget.text
            self.app.copy_to_clipboard(current_data)

            next_data = queue_list.pop(0)
            footer = self.query_one(f"#{editor_id} CustomTranscriptFooter", CustomTranscriptFooter)
            footer.queue_count = len(queue_list)

            transcript_widget.text = next_data

        elif transcript_widget.text != "":
            current_data = transcript_widget.text
            self.app.copy_to_clipboard(current_data)
            transcript_widget.text = ""
        else:
            self.notify("Nothing to grab in transcript box!")

    def action_grab_mic_transcript(self) -> None:
        self._grab_transcript("transcript", "transcript-editor", self.transcript_queue_mic)

    def action_grab_loopback_transcript(self) -> None:
        self._grab_transcript("transcript-loopback", "transcript-editor-loopback", self.transcript_queue_loopback)

    # push the control popup
    def action_open_popup(self) -> None:
        self.app.push_screen(PopupComponent(), callback=self._on_file_selected)

    def _on_file_selected(self, path) -> None:
        """Called when popup dismisses. path is a Path object or None."""
        if path is not None:
            self.load_file(path)

    def _apply_loaded_file(self, file_path: str, content: str) -> None:
        """Apply loaded content to the UI (runs on main thread)."""
        user_input_widget = self.query_one("#user", TextArea)
        user_input_widget.text = content
        self.current_file_path = file_path
        self.is_saved = True

    # watches for reactive components, id by the name of the func
    def watch_current_file_path(self, new_path: str) -> None:
        """Update border title when file path changes."""
        self._update_border_title()

    def watch_is_saved(self, saved: bool) -> None:
        """Update border title when save state changes."""
        self._update_border_title()

    def _update_border_title(self) -> None:
        """Set the UserInputArea border title to reflect file name and save state."""
        user_input_widget = self.query_one("#user", TextArea)
        if self.current_file_path:
            name = Path(self.current_file_path).name
            prefix = "● " if not self.is_saved else ""
            user_input_widget.border_title = f"{prefix}{name}"
        else:
            user_input_widget.border_title = "Input"

    def action_save_file(self) -> None:
        """Save current content back to disk."""
        if not self.current_file_path:
            self.notify("No file open to save", severity="warning")
            return
        user_input_widget = self.query_one("#user", TextArea)
        self._save_file_to_disk(self.current_file_path, user_input_widget.text)

    def _on_save_complete(self) -> None:
        """Called after successful save."""
        self.is_saved = True
        self.notify("Saved")

    # toggles record for mic recording
    def action_toggle_record(self) -> None:
        self.is_recording = not self.is_recording
        mic_widget = self.query_one('#transcript', TextArea)

        if self.is_recording:
            mic_widget.border_title = "🔴 Mic Recording"
            self.record()
        else:
            mic_widget.border_title = "⚪ Mic Idle"
            self.stop_record()

    def action_toggle_loopback_record(self) -> None:
        self.is_loopback_recording = not self.is_loopback_recording
        loopback_widget = self.query_one('#transcript-loopback', TextArea)

        if self.is_loopback_recording:
            loopback_widget.border_title = "🔴 Loopback Recording"
            self.record_loopback()
        else:
            loopback_widget.border_title = "⚪ Loopback Idle"
            self.stop_record_loopback()


            
    # --------------------------------------- Compose -------------------------------------------------
    def compose(self) -> ComposeResult:
        # yield TopBar(id="top-bar")
        with Horizontal(id="main-row"):
            yield UserInputArea(show_line_numbers=True, id="user")
            with Container(id="right-column"):
                yield MasterMarkdown(id="master")
                with Horizontal(id="transcript-row"):
                    yield TranscriptEditor(id="transcript-editor")
                    yield TranscriptEditor(transcript_id="transcript-loopback", id="transcript-editor-loopback")

        with Horizontal(id="bottom-bar"):
            yield Footer()


    # --------------------------------------- Workers -------------------------------------------------
    # this is the transcription worker, it is a thread and it always on but it just sleeps if nothing to do in queue
    @work(thread=True)
    def transcription_loop_mic(self):
        worker = get_current_worker()
        while not worker.is_cancelled:
            try:
                clip = self.audio_queue_mic.get(timeout=3)
                result, info = self.transcript_model.transcribe(clip)
                text = " ".join(segment.text for segment in result)
                self.app.call_from_thread(self.append_transcript_mic, text)
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
                self.app.call_from_thread(self.append_transcript_loopback, text)
            except queue.Empty:
                continue

    @work(thread=True)
    def _save_file_to_disk(self, file_path: str, content: str) -> None:
        """Write content to disk in a background thread."""
        worker = get_current_worker()
        try:
            Path(file_path).write_text(content, encoding="utf-8")
            if not worker.is_cancelled:
                self.app.call_from_thread(self._on_save_complete)
        except Exception as e:
            if not worker.is_cancelled:
                self.app.call_from_thread(self.notify, f"Failed to save: {e}", severity="error")

    @work(thread=True)
    def load_file(self, path: Path) -> None:
        """Read file from disk in a background thread."""
        worker = get_current_worker()
        try:
            content = path.read_text(encoding="utf-8")
            if not worker.is_cancelled:
                self.app.call_from_thread(self._apply_loaded_file, str(path), content)
        except Exception as e:
            if not worker.is_cancelled:
                self.app.call_from_thread(self.notify, f"Failed to load: {e}", severity="error")

    # so before transcription worker loop would append to a queue.Queue in which then the main UI thread needs to do wonky stuff on but it is not flexible
    # before transcription loop pushed to a thread safe queue.Queue which is an object from self (can only do this bc it is queue.Queue if it was [] then it is race cond)
    # now the transcription loop will just get the data and then call from thread to call a callback and that callback will RUN ON THE UI Thread but if we keep the footprint of this callback fun low then it should not block
    # it will just get the trans str and append it to a local queue (not thread safe one)
    # workflow is like | transcription_loop detects new | -> | calls callback | -> | callback checks if transcript has somethign there rn | -> | | -> | |
    # so then the event manager that handles the transfer transcript to user input will copy and paste and then blank out the transcript and then if queue len > 1 then pop and use else leave it blank
    def _append_transcript(self, widget_id: str, editor_id: str, queue_list: list, transcribed_text: str):
        """Generic append logic for either mic or loopback transcript."""
        transcript_widget = self.query_one(f'#{widget_id}', TextArea)

        if transcript_widget.text == "":
            transcript_widget.text = transcribed_text
        else:
            queue_list.append(transcribed_text)
            footer = self.query_one(f"#{editor_id} CustomTranscriptFooter", CustomTranscriptFooter)
            footer.queue_count = len(queue_list)

    def append_transcript_mic(self, transcribed_text):
        self._append_transcript("transcript", "transcript-editor", self.transcript_queue_mic, transcribed_text)

    def append_transcript_loopback(self, transcribed_text):
        self._append_transcript("transcript-loopback", "transcript-editor-loopback", self.transcript_queue_loopback, transcribed_text)


    # -----------------------------------------Record-----------------------------------------------

    # for mic recording
    def record(self) -> None:
        '''
        Start the record only when current recorder recording status is false
        '''
        if self.recorder.get_recording_status() == False:
            self.recorder.start_recording()
    
    def stop_record(self) -> None:
        if self.recorder.get_recording_status() == True:
            temp_audio = self.recorder.stop_recording()
            self.audio_queue_mic.put(temp_audio)

    # for loop back recording
    def record_loopback(self) -> None:
        if self.loopback_recorder.get_recording_status() == False:
            self.loopback_recorder.start_recording()
    
    def stop_record_loopback(self) -> None:
        if self.loopback_recorder.get_recording_status() == True:
            temp_audio = self.loopback_recorder.stop_recording()

            # !! TEMP: save as wav for debugging
            import wave
            sr = int(self.loopback_recorder._loopback['defaultSampleRate'])
            raw_int16 = (temp_audio * 32768).astype(np.int16)
            with wave.open("debug_loopback.wav", "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(raw_int16.tobytes())
            self.notify(f"Saved debug_loopback.wav ({len(temp_audio)} samples, {sr}Hz)")

            self.audio_queue_loopback.put(temp_audio)