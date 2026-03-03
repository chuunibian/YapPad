from dataclasses import dataclass
import sounddevice as sd
import queue
import numpy as np

@dataclass
class SDParam:
    sample_rate: int
    channels: int
    dtype: str

class AudioCaptureT:

    '''
        Atp I think it is good enough for the inputstream thread to rep call the callback and then the queue hsould have data and then
        when the stop rec is called just use that, I think no need to poll

        Also treating this as a create one and reuse so __init__ will not start the stream
        This comes with implicaiton so need to avoid spamming, for like clips longer than 5 sec I htink it is ok
    
    
    '''

    def __init__(self, params: SDParam):
        self.input_params = params

        self._samples_queue = queue.Queue()
        self._chunks = []
        self._recording_flag = False # on init rec should be false

        self._sdconsumer = None


    # callback for the sd lbrary consumer which will input whatever it consumed into here
    def _callback(self, indata, frames, time, status):
        if status:
            print(status)
        
        self._samples_queue.put(indata.copy()) # need to copy since the buffer is internal and singular


    def stop_recording(self):
        self._recording_flag = False

        # for now stop and the close as well, but in future maybe can do some pause like action
        self._sdconsumer.stop()
        self._sdconsumer.close()
        self._sdconsumer = None

        chunks = []
        while not self._samples_queue.empty():
            # try is for any possible reason why queue would be messed with even tho the only thread managing it was destroyed
            try:
                chunks.append(self._samples_queue.get_nowait())
            except queue.Empty:
                break

        return np.concatenate(chunks, axis=0).flatten()


    
    def start_recording(self):
        '''
        Start recording should make the _sdconsumer and then start the thread to do the processing
        
        to avoid issues need to check if it is currently already recording, leaving that up to UI
        '''
        self._recording_flag = True

        # clear queue
        self._clear_queue()

        # this will create a consumer thread
        self._sdconsumer = sd.InputStream(samplerate=self.input_params.sample_rate, channels=self.input_params.channels, callback=self._callback)

        # start the thread
        self._sdconsumer.start()


    def get_recording_status(self):
        return self._recording_flag
    

    # clears queue
    def _clear_queue(self):
        while not self._samples_queue.empty():
            try:
                self._samples_queue.get_nowait()
            except queue.Empty:
                break



