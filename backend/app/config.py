import os
from dotenv import load_dotenv

load_dotenv()

# One NVIDIA key per capability, so usage and limits are tracked separately.
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
KEY_CHAT = os.getenv("NVIDIA_KEY_RAG", "")          # chat model for RAG answers, polishing
KEY_EMBED = os.getenv("NVIDIA_KEY_EMBED", "")
KEY_TRANSLATE = os.getenv("NVIDIA_KEY_TRANSLATE", "")
KEY_TTS = os.getenv("NVIDIA_KEY_TTS", "")
KEY_STT = os.getenv("NVIDIA_KEY_STT", "")

# Models checked live on 2026-10-30. NVIDIA retires models, so these are env-overridable.
CHAT_MODEL = os.getenv("NVIDIA_CHAT_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")
EMBED_MODEL = os.getenv("NVIDIA_EMBED_MODEL", "nvidia/nemotron-3.5-embed-1b")
TRANSLATE_MODEL = os.getenv("NVIDIA_TRANSLATE_MODEL", "nvidia/riva-translate-4b-instruct-v2")
TTS_URL = os.getenv("NVIDIA_TTS_URL", "https://877104f7-e885-42b9-8de8-f6e4c6303969.invocation.api.nvcf.nvidia.com/v1/audio/synthesize")
STT_FUNCTION_ID = os.getenv("NVIDIA_STT_FUNCTION_ID", "71203149-d3b7-4460-8231-1be2543a1fca")
STT_SERVER = "grpc.nvcf.nvidia.com:443"

# Reported trial limit is ~40 requests/min; we throttle ourselves below it.
RPM_LIMIT = int(os.getenv("NVIDIA_RPM_LIMIT", "35"))
HTTP_TIMEOUT_S = float(os.getenv("HTTP_TIMEOUT_S", "20"))

BHASHINI_USER_ID = os.getenv("BHASHINI_USER_ID", "")
BHASHINI_ULCA_API_KEY = os.getenv("BHASHINI_ULCA_API_KEY", "")
BHASHINI_CONFIG_URL = os.getenv(
    "BHASHINI_CONFIG_URL",
    "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline",
)

# Pipeline id comes from the ULCA portal / Pipeline Search call. The default is the one seen in
# community code, not in the official docs, so confirm it for your account.
BHASHINI_PIPELINE_ID = os.getenv("BHASHINI_PIPELINE_ID", "64392f96daac500b55c543cd")

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "dev-only-secret")
DB_PATH = os.getenv("DB_PATH", "rti.db")

MAX_DRAFT_CHARS = 3000
RTI_FEE_INR = 10
