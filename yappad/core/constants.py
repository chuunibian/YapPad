# ─── Whisper Models ──────────────────────────────────────────────
WHISPER_MODELS = [
    ("Tiny", "tiny"),
    ("Base", "base"),
    ("Small", "small"),
    ("Medium", "medium"),
    ("Large v1", "large-v1"),
    ("Large v2", "large-v2"),
    ("Large v3 (slowest, most accurate)", "large-v3"),
    ("Distil Large v3", "distil-large-v3"),
    ("Turbo (fast + accurate)", "turbo"),
]

# ─── Device Options ──────────────────────────────────────────────
DEVICES = [
    ("CPU", "cpu"),
    ("CUDA (GPU)", "cuda"),
]

# ─── Audio Sample Rates ─────────────────────────────────────────
WHISPER_SAMPLE_RATE = 16000
DEFAULT_MIC_SAMPLE_RATE = 16000
DEFAULT_LOOPBACK_SAMPLE_RATE = 48000

# ─── Defaults (used by AppConfig / WhisperModelConfig) ───────────
DEFAULT_WHISPER_MODEL = "base"
DEFAULT_COMPUTE_TYPE = "cpu"
DEFAULT_DEVICE = "cpu"


# ModelSizeTiny~75 MBBase~145 MBSmall~465 MBMedium~1.5 GBLarge v1/v2/v3~3.1 GBDistil Large v3~1.5 GBTurbo~1.6 GB
