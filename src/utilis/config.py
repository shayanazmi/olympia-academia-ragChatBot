"""
Centralized configuration for Olympia Academia
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ══════════════════════════════════════════════════════════════════════════════
# PATH CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

# Base directories
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DB_DIR = DATA_DIR / "db"

# Ensure directories exist
for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, DB_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# DATABASE FILES (Your existing naming convention)
# ══════════════════════════════════════════════════════════════════════════════

# Index files - using your EXACT names
FAISS_INDEX_PATH = DB_DIR / "olympia_vectors.index"
BM25_INDEX_PATH = DB_DIR / "olympia_bm25.pkl"
DOCUMENTS_PATH = DB_DIR / "olympia_docs.pkl"

# Excel/CSV files
ENRICHED_DATA_PATH = PROCESSED_DATA_DIR / "olympia_enriched.xlsx"
RAW_LINKS_PATH = RAW_DATA_DIR / "extracted_links.csv"

# ══════════════════════════════════════════════════════════════════════════════
# MODEL CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

# Ollama settings
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-v3")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))

# Embedding model
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", 
    "sentence-transformers/all-MiniLM-L6-v2"
)
EMBEDDING_DIMENSION = 384  # for all-MiniLM-L6-v2

# ══════════════════════════════════════════════════════════════════════════════
# PROCESSING CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

# Batch processing
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "5"))

# Text processing
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
MIN_CONTENT_LENGTH = 50

# Rate limiting
MAX_REQUESTS_PER_MINUTE = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "30"))
DAILY_USER_QUOTA = int(os.getenv("DAILY_USER_QUOTA", "100"))

# ══════════════════════════════════════════════════════════════════════════════
# SEARCH CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

# Retrieval settings
TOP_K_RESULTS = 5
HYBRID_ALPHA = 0.7  # Weight for semantic search (0.3 for keyword)
SIMILARITY_THRESHOLD = 0.3

# Response generation
MAX_RESPONSE_TOKENS = 1024
TEMPERATURE = 0.7
SYSTEM_PROMPT = """You are Olympia, an AI assistant specializing in information 
from a curated knowledge base. Provide accurate, helpful responses based on the 
context provided. If the information isn't in the context, say so."""

# ══════════════════════════════════════════════════════════════════════════════
# UI CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

APP_TITLE = "🏛️ Olympia Academia"
APP_SUBTITLE = "Your Private Knowledge Assistant"
SIDEBAR_TITLE = "Knowledge Base Stats"

# Chat interface
MAX_CHAT_HISTORY = 80
WELCOME_MESSAGE = """Welcome to Olympia Academia! 🎓

I can help you find information from your curated knowledge base. 
Ask me anything about the content we've indexed!"""