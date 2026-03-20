import pyaudiowpatch as pyaudio
from .loopback_consumer import DeviceLoopbackCaptureT, PyAWParam


class LoopbackEngine:
    def __init__(self, param):
        self.recorder = DeviceLoopbackCaptureT(param)  # param is PyAWParam
        self._pyaudio = self.recorder.pyaudio_manager  # reuse the same PyAudio instance

    def switch_device(self, device_name):
        """switches the loopback device by name string
        resolves name to the pyaudiowpatch device info dict and updates consumer
        """
        device_info = self.find_device_info(device_name)
        if device_info is not None:
            self.recorder.change_loopback_device(device_info)

    def get_devices(self) -> list[dict]:
        """
        Returns list of WASAPI loopback devices with friendly UI labels.
        Loopback devices are output devices that can be captured.

        Example return:
        [
            {
                'index': 5,
                'name': 'Speakers (Realtek Audio) [Loopback]',
                'channels': 2,
                'samplerate': 48000,
                'label': 'Speakers (Realtek Audio) [Loopback]'
            },
            ...
        ]
        """
        ui_ret = []
        host_api_count = self._pyaudio.get_host_api_count()

        # fallback if WASAPI info unavailable
        try:
            wasapi_info = self._pyaudio.get_host_api_info_by_type(pyaudio.paWASAPI)
        except OSError:
            return ui_ret

        for i in range(self._pyaudio.get_device_count()):
            try:
                device = self._pyaudio.get_device_info_by_index(i)
                # Check if it's a WASAPI loopback device
                if device.get("hostApi") == wasapi_info["index"] and device.get(
                    "isLoopbackDevice", False
                ):
                    ui_ret.append(
                        {
                            "index": device["index"],
                            "name": device["name"],
                            "channels": device[
                                "maxInputChannels"
                            ],  # Loopbacks are inputs
                            "samplerate": int(device["defaultSampleRate"]),
                            "label": device["name"],
                        }
                    )
            except Exception:
                continue

        return ui_ret

    def get_default_device(self):
        """
        Returns the default WASAPI loopback device name for UI display

        Example return: 'Speakers (Realtek Audio) [Loopback]'
        """
        try:
            loopback = self._pyaudio.get_default_wasapi_loopback()
            return loopback["name"]
        except Exception:
            return "No loopback device found"

    def find_device_info(self, name: str):
        """
        Finds a loopback device info dict by name.
        Returns the full pyaudiowpatch device info dict or None.
        """
        try:
            wasapi_info = self._pyaudio.get_host_api_info_by_type(pyaudio.paWASAPI)
        except OSError:
            return None

        for i in range(self._pyaudio.get_device_count()):
            try:
                device = self._pyaudio.get_device_info_by_index(i)
                if device.get("hostApi") == wasapi_info["index"] and device.get(
                    "isLoopbackDevice", False
                ):
                    if device["name"] == name:
                        return device
            except Exception:
                continue

        return None

    def start_recording(self):
        self.recorder.start_recording()

    def stop_recording(self):
        return self.recorder.stop_recording()

    def get_recording_status(self):
        return self.recorder.get_recording_status()
