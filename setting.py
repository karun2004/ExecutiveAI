"""
MACH-1 Configuration
Loads .env and provides typed settings to all modules.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Find project root (where .env lives)
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _int(key: str, default: int = 0) -> int:
    return int(os.getenv(key, str(default)))


# ── Paths ──────────────────────────────────────────
MACH1_HOME = Path(_env("MACH1_HOME", str(PROJECT_ROOT)))
DATA_DIR = Path(_env("DATA_DIR", str(PROJECT_ROOT / "data")))
LOG_DIR = Path(_env("LOG_DIR", str(PROJECT_ROOT / "logs")))
BACKUP_DIR = Path(_env("BACKUP_DIR", str(PROJECT_ROOT / "backups")))
DB_PATH = DATA_DIR / "mach1.db"

# Ensure directories exist
for d in [DATA_DIR, LOG_DIR, BACKUP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── API Keys ───────────────────────────────────────
GROQ_API_KEY = _env("GROQ_API_KEY")
MISTRAL_API_KEY = _env("MISTRAL_API_KEY")
GOOGLE_AI_KEY = _env("GOOGLE_AI_KEY")

# ── Models ─────────────────────────────────────────
GROQ_MODEL = _env("GROQ_MODEL", "llama-3.3-70b-versatile")
MISTRAL_CHAT_MODEL = _env("MISTRAL_CHAT_MODEL", "mistral-large-latest")
MISTRAL_CODE_MODEL = _env("MISTRAL_CODE_MODEL", "codestral-latest")
OLLAMA_CHAT_MODEL = _env("OLLAMA_CHAT_MODEL", "mistral:7b")
OLLAMA_CODE_MODEL = _env("OLLAMA_CODE_MODEL", "qwen2.5-coder:7b")
GOOGLE_MODEL = _env("GOOGLE_MODEL", "gemini-2.0-flash")
OLLAMA_HOST = _env("OLLAMA_HOST", "http://localhost:11434")

# ── Flask ──────────────────────────────────────────
FLASK_HOST = _env("FLASK_HOST", "0.0.0.0")
FLASK_PORT = _int("FLASK_PORT", 5000)
FLASK_SECRET_KEY = _env("FLASK_SECRET_KEY", "dev-key-change-me")

# ── GitHub ─────────────────────────────────────────
GITHUB_TOKEN = _env("GITHUB_TOKEN")
GITHUB_USERNAME = _env("GITHUB_USERNAME")

# ── Notifications ──────────────────────────────────
NTFY_TOPIC = _env("NTFY_TOPIC", "mach1-alerts")
NTFY_SERVER = _env("NTFY_SERVER", "https://ntfy.sh")

# ── Rate Limits ────────────────────────────────────
GROQ_RPD = _int("GROQ_RPD", 1000)
GOOGLE_RPD = _int("GOOGLE_RPD", 250)
MISTRAL_RPS = _int("MISTRAL_RPS", 1)

# ── Schedule ───────────────────────────────────────
HEALTH_CHECK_HOUR = _int("HEALTH_CHECK_HOUR", 23)
HEALTH_CHECK_MINUTE = _int("HEALTH_CHECK_MINUTE", 0)
BACKUP_HOUR = _int("BACKUP_HOUR", 23)
BACKUP_MINUTE = _int("BACKUP_MINUTE", 10)

# ── Team → Model Mapping ──────────────────────────
# Each team gets a primary provider + model and a fallback chain
TEAM_MODELS = {
    "ceo": {
        "chain": [
            ("groq", GROQ_MODEL),
            ("mistral", MISTRAL_CHAT_MODEL),
            ("ollama", OLLAMA_CHAT_MODEL),
        ]
    },
    "content": {
        "chain": [
            ("groq", GROQ_MODEL),
            ("mistral", MISTRAL_CHAT_MODEL),
            ("ollama", OLLAMA_CHAT_MODEL),
        ]
    },
    "coding": {
        "chain": [
            ("mistral", MISTRAL_CODE_MODEL),
            ("groq", GROQ_MODEL),
            ("ollama", OLLAMA_CODE_MODEL),
        ]
    },
    "devops": {
        "chain": [
            ("mistral", MISTRAL_CHAT_MODEL),
            ("groq", GROQ_MODEL),
            ("ollama", OLLAMA_CHAT_MODEL),
        ]
    },
    "marketing": {
        "chain": [
            ("groq", GROQ_MODEL),
            ("mistral", MISTRAL_CHAT_MODEL),
            ("ollama", OLLAMA_CHAT_MODEL),
        ]
    },
    "sales": {
        "chain": [
            ("mistral", MISTRAL_CHAT_MODEL),
            ("groq", GROQ_MODEL),
            ("ollama", OLLAMA_CHAT_MODEL),
        ]
    },
}

# Google is always LAST resort — appended dynamically by the router
GOOGLE_FALLBACK = ("google", GOOGLE_MODEL)
