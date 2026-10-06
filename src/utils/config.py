"""
Centralized configuration for Olympia Academia
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ══════════════════════════════════════════════════════════════════════════════
# PATH CONFIGURATION (Dynamic, Portable)
# ══════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DB_DIR = DATA_DIR / "db"
BACKUP_DIR = DATA_DIR / "backups"

# Ensure runtime directories exist
for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, DB_DIR, BACKUP_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# DATABASE FILES
# ══════════════════════════════════════════════════════════════════════════════

FAISS_INDEX_PATH = DB_DIR / "olympia_vectors.index"
BM25_INDEX_PATH = DB_DIR / "olympia_bm25.pkl"
DOCUMENTS_PATH = DB_DIR / "olympia_docs.pkl"

ENRICHED_DATA_PATH = PROCESSED_DATA_DIR / "oa_enriched.xlsx"
CLEANED_DATA_PATH = PROCESSED_DATA_DIR / "oa_cleaned.xlsx"
RAW_LINKS_PATH = RAW_DATA_DIR / "whatsapp_links_unique.xlsx"

# ══════════════════════════════════════════════════════════════════════════════
# NVIDIA NIM API CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

# Optimal Models for Academic RAG
NVIDIA_PRIMARY_MODEL = os.getenv("NVIDIA_PRIMARY_MODEL", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning")
NVIDIA_FAST_MODEL = os.getenv("NVIDIA_FAST_MODEL", "meta/llama-3.2-11b-vision-instruct")
NVIDIA_TIMEOUT = int(os.getenv("NVIDIA_TIMEOUT", "60"))

# Embedding model
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIMENSION = 384

# ══════════════════════════════════════════════════════════════════════════════
# SEARCH & RETRIEVAL CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_TOP_K = 5
MAX_CANDIDATES = 15
VECTOR_WEIGHT = 0.4
BM25_WEIGHT = 0.6

# Text processing
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
MIN_CONTENT_LENGTH = 50

# Rate limiting
DAILY_USER_QUOTA = int(os.getenv("DAILY_USER_QUOTA", "100"))

# ══════════════════════════════════════════════════════════════════════════════
# UI CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

APP_TITLE = "🏛️ Olympia Academia"
APP_SUBTITLE = "Your Context-Aware Research Assistant"
MAX_CHAT_HISTORY = 80
