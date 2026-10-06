"""
Olympia Academia - Utilities Module
"""

from .config import (
    PROJECT_ROOT,
    DATA_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    DB_DIR,
    FAISS_INDEX_PATH,
    BM25_INDEX_PATH,
    DOCUMENTS_PATH,
    ENRICHED_DATA_PATH,
    CLEANED_DATA_PATH,
    RAW_LINKS_PATH,
    NVIDIA_BASE_URL,
    NVIDIA_API_KEY,
    NVIDIA_PRIMARY_MODEL,
    NVIDIA_FAST_MODEL,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    DEFAULT_TOP_K,
    VECTOR_WEIGHT,
    BM25_WEIGHT,
    APP_TITLE,
    APP_SUBTITLE,
)

from .nim_client import (
    NIMClient,
    NIMAuthenticationError,
    NIMRateLimitError,
)

from .limit_checker import (
    init_limits_db,
    check_and_update_limit,
)

__all__ = [
    'PROJECT_ROOT',
    'DATA_DIR',
    'RAW_DATA_DIR',
    'PROCESSED_DATA_DIR',
    'DB_DIR',
    'FAISS_INDEX_PATH',
    'BM25_INDEX_PATH',
    'DOCUMENTS_PATH',
    'ENRICHED_DATA_PATH',
    'CLEANED_DATA_PATH',
    'RAW_LINKS_PATH',
    'NVIDIA_BASE_URL',
    'NVIDIA_API_KEY',
    'NVIDIA_PRIMARY_MODEL',
    'NVIDIA_FAST_MODEL',
    'EMBEDDING_MODEL',
    'EMBEDDING_DIMENSION',
    'DEFAULT_TOP_K',
    'VECTOR_WEIGHT',
    'BM25_WEIGHT',
    'APP_TITLE',
    'APP_SUBTITLE',
    'NIMClient',
    'NIMAuthenticationError',
    'NIMRateLimitError',
    'init_limits_db',
    'check_and_update_limit',
]
