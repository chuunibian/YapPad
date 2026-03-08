import sounddevice as sd
from .sd_consumer import AudioCaptureT, SDParam


class sdEngine():

    def __init__(self, param):
        self.recorder = AudioCaptureT(param) # param is SDParam


    def switch_device(self, device_name):
        ''' switches the user selected device by name string
            resolves name to index and updates consumer
        '''
        device_index = self.find_device_index(device_name)
        if device_index != -1:
            self.recorder.change_current_device(device_index)


    def switch_inputstream_parameters(self, param):
        '''
        wrapper for switching other parameters
        '''
        self.recorder.change_params(param)


    def get_devices(self) -> list[dict]:
        '''
        Returns list of devices with friendly UI string mapped to backend identifiable value

        Example return:
        [
            {
                'index': 1,
                'name': 'Microphone (Realtek Audio)',
                'hostapi': 'Windows WASAPI',
                'channels': 2,
                'samplerate': 44100,
                'label': 'Microphone (Realtek Audio) (Windows WASAPI)'
            },
            ...
        ]
        '''
        devices = sd.query_devices()
        hostapis = sd.query_hostapis()
        ui_ret = []
        for index, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                ui_ret.append({
                    'index': index,
                    'name': device['name'],
                    'hostapi': hostapis[device['hostapi']]['name'],
                    'channels': device['max_input_channels'],
                    'samplerate': int(device['default_samplerate']),
                    'label': f"{device['name']} ({hostapis[device['hostapi']]['name']})"
                })
        return ui_ret

    def get_default_device(self):
        '''
        Returns the default input device info for UI display

        Example return:
        {
            'default_name': 'Microphone (Realtek Audio)',
            'api_name': 'Windows WASAPI'
        }
        '''
        default_info = sd.query_devices(kind='input') # gives default
        hostapis = sd.query_hostapis()
        api_name = hostapis[default_info['hostapi']]['name']
        return {
            "default_name": default_info['name'],
            "api_name": api_name
        }
        
    def find_device_index(self, name: str) -> int:
        devices = sd.query_devices()
        for index, device in enumerate(devices):
            if device['name'] == name and device['max_input_channels'] > 0:
                return index

        return -1

    def start_recording(self):
        self.recorder.start_recording()

    def stop_recording(self):
        return self.recorder.stop_recording()

    def get_recording_status(self):
        return self.recorder.get_recording_status()
