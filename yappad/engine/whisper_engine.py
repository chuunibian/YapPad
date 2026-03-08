# import the dataclass stuff
import threading
import gc
from faster_whisper import WhisperModel
from huggingface_hub import scan_cache_dir


class TranscriptionEngine():
    def __init__(self):
        '''
        Will hold the master ref to faster whisper object
        '''
        self.transcript_model = WhisperModel("base", device="cpu", compute_type="int8") # master object

        # basic temp workarodun for thread to give back errors
        self.load_status = 0  # 0: Idle, 1: Loading, 2: Success, -1: Error
        self.last_error = ""

        self.current_model = "base"


    def switch_model_helper(self, param):
        '''
        This may block ui thread
        so possibly need to run it as a thread

        '''

        self.load_status = 1
        self.transcript_model = None
        gc.collect() # force garbage collection since prev model should have no live ref

        try:
            self.transcript_model = WhisperModel(param.model_size_or_path, param.device, param.compute_type)
            self.load_status = 2
            self.current_model = param.model_size_or_path
        except ValueError as e:
            print(f"Configuration error (usually compute_type or device): {e}")
            self.load_status = -1
            self.last_error = str(e)
        except RuntimeError as e:
            print(f"Hardware or Driver error (Out of memory or missing CUDA files): {e}")
            self.load_status = -1
            self.last_error = str(e)
        except Exception as e:
            print(f"Something else went wrong (Network issue? Bad model path?): {e}")
            self.load_status = -1
            self.last_error = str(e)

    def switch_model(self, param):
        '''
        This may block ui thread
        so possibly need to run it as a thread

        this func also return instantly so need to prevent double clicks which will start multipl threads that is bad


        also if selected model is not downloaded this function could take a lot of time, maybe have some way to tell UI it is not ready 
        and for it to have a loading bar (in general nice to have the loading when switching models)

        '''

        if self.load_status == 1:
            return

        switch_T = threading.Thread(
                target=self.switch_model_helper, 
                args=(param,), 
                daemon=True
            )
        switch_T.start()


    def get_status(self):
        '''
        Return the current status of the model in the engine, if it is success then that means the live new model went in
        if not then an error has happened

        '''
        return self.load_status


    def get_current_model(self):

        return self.current_model

    # TODO check this and change if neeeded
    def get_downloaded_models() -> set[str]:
        '''
        Scans the HuggingFace cache for already-downloaded faster-whisper models.
        Returns a set of model name strings, e.g. {"base", "small", "large-v3"}.
        '''
        try:
            cache_info = scan_cache_dir()
            downloaded = set()
            for repo in cache_info.repos:
                if repo.repo_id.startswith("Systran/faster-whisper-"):
                    model_name = repo.repo_id.replace("Systran/faster-whisper-", "")
                    downloaded.add(model_name)
            return downloaded
        except Exception:
            return set()


    def transcribe(self, clip):
        return self.transcript_model.transcribe(clip)
