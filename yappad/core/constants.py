

# ─── Whisper Models ──────────────────────────────────────────────
WHISPER_MODELS = [
    ("Tiny (fastest, least accurate)",    "tiny"),
    ("Base (good balance)",               "base"),
    ("Small",                             "small"),
    ("Medium",                            "medium"),
    ("Large v1",                          "large-v1"),
    ("Large v2",                          "large-v2"),
    ("Large v3 (slowest, most accurate)", "large-v3"),
    ("Distil Large v3",                   "distil-large-v3"),
    ("Turbo (fast + accurate)",           "turbo"),
]

# ─── Compute Types ───────────────────────────────────────────────
COMPUTE_TYPES = [
    ("INT8 (fastest, CPU-friendly)", "int8"),
    ("Float16 (GPU recommended)",    "float16"),
    ("Float32 (most precise)",       "float32"),
]

# ─── Device Options ──────────────────────────────────────────────
DEVICES = [
    ("CPU",          "cpu"),
    ("CUDA (GPU)",   "cuda"),
    ("Auto Detect",  "auto"),
]

# ─── Layout Modes ────────────────────────────────────────────────
LAYOUT_MODES = [
    ("Editor Only", "editor"),
    ("Mic Mode",    "mic"),
    ("Loopback",    "loopback"),
    ("Full",        "full"),
]

# ─── Audio Source ────────────────────────────────────────────────
AUDIO_SOURCES = [
    ("Microphone",    "mic"),
    ("Device Audio",  "device"),
    ("Both",          "both"),
]

# ─── Detection Modes ────────────────────────────────────────────
DETECT_MODES = [
    ("Auto Detect Silence", "auto"),
    ("Manual Trigger",      "manual"),
]

# ─── Audio Sample Rates ─────────────────────────────────────────
WHISPER_SAMPLE_RATE = 16000
DEFAULT_MIC_SAMPLE_RATE = 16000
DEFAULT_LOOPBACK_SAMPLE_RATE = 48000

# ─── Defaults (used by AppConfig / WhisperModelConfig) ───────────
DEFAULT_WHISPER_MODEL = "base"
DEFAULT_COMPUTE_TYPE = "int8"
DEFAULT_DEVICE = "cpu"
