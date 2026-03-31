from dataclasses import dataclass
import pyaudiowpatch as pyaudio
import queue
import numpy as np
from scipy.signal import resample
from ..core.constants import WHISPER_SAMPLE_RATE


@dataclass
class PyAWParam:
    sample_rate: int
    channels: int


class DeviceLoopbackCaptureT:
    def __init__(self, params: PyAWParam):
        self.input_params = params  # currently unsed

        self._samples_queue = queue.Queue()
        self._recording_flag = False  # on init rec should be false

        self.pyaudio_manager = pyaudio.PyAudio()
        self._temp_stream = None  # temp var for the stream return

        # gets the default loopback device
        self._loopback = self.pyaudio_manager.get_default_wasapi_loopback()

    def change_loopback_device(self, device_info):
        """
        Swaps the internal loopback device dict.
        device_info should be a pyaudiowpatch device info dict and then this new info dict is used to start rec
        """
        self._loopback = device_info

    # similar to theother library one the call backis called when the buffer size is filled for the pyaudoawtch thread
    def _callback(self, in_data, frame_count, time_info, status_flags):

        self._samples_queue.put(in_data)

        return (None, pyaudio.paContinue)

    def stop_recording(self):
        self._recording_flag = False

        self._temp_stream.stop_stream()
        self._temp_stream.close()
        self._temp_stream = None

        chunks = []
        while not self._samples_queue.empty():
            try:
                chunks.append(self._samples_queue.get_nowait())
            except queue.Empty:
                break

        raw_bytes = b"".join(chunks)

        # guard: if nothing was captured (absolute silence / instant stop),
        # return an empty array to avoid divide-by-zero in resample
        if len(raw_bytes) == 0:
            return np.array([], dtype=np.float32)

        audio = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        # stereo to mono since a needed conversion
        if self._loopback["maxInputChannels"] > 1:
            audio = audio.reshape(-1, self._loopback["maxInputChannels"]).mean(axis=1)

        # resample from device rate (e.g. 48kHz) to 16kHz for Whisper
        # this is for resampling temporary sorta can improve
        device_sr = int(self._loopback["defaultSampleRate"])
        if device_sr != WHISPER_SAMPLE_RATE:
            num_samples_16k = int(len(audio) * WHISPER_SAMPLE_RATE / device_sr)
            audio = resample(audio, num_samples_16k).astype(np.float32)

        return audio

    def start_recording(self):
        self._recording_flag = True

        # clear queue
        self._clear_queue()

        # open a stream
        self._temp_stream = self.pyaudio_manager.open(
            format=pyaudio.paInt16,
            channels=self._loopback["maxInputChannels"],
            rate=int(self._loopback["defaultSampleRate"]),
            input=True,
            input_device_index=self._loopback["index"],
            frames_per_buffer=1024,
            stream_callback=self._callback,
        )

        self._temp_stream.start_stream()

    def get_recording_status(self):
        return self._recording_flag

    # clears queue
    def _clear_queue(self):
        while not self._samples_queue.empty():
            try:
                self._samples_queue.get_nowait()
            except queue.Empty:
                break
