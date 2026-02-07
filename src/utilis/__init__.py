"""
Olympia Academia - Utilities Module
====================================

This module provides shared utilities, configuration, and helper functions.

Components:
-----------
- config: Centralized configuration settings
- evaluate_system: RAG evaluation and testing
- limit_checker: User quota management

Author: Olympia Academia Team
"""

__version__ = "1.0.0"
__author__ = "Olympia Academia Team"

# Import configuration
from .config import (
    # Paths
    PROJECT_ROOT,
    DATA_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    DB_DIR,
    
    # Database files
    FAISS_INDEX_PATH,
    BM25_INDEX_PATH,
    DOCUMENTS_PATH,
    ENRICHED_DATA_PATH,
    RAW_LINKS_PATH,
    
    # Model settings
    OLLAMA_HOST,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    
    # Processing settings
    BATCH_SIZE,
    MAX_WORKERS,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    MIN_CONTENT_LENGTH,
    MAX_REQUESTS_PER_MINUTE,
    DAILY_USER_QUOTA,
    
    # Search settings
    TOP_K_RESULTS,
    HYBRID_ALPHA,
    SIMILARITY_THRESHOLD,
    MAX_RESPONSE_TOKENS,
    TEMPERATURE,
    SYSTEM_PROMPT,
    
    # UI settings
    APP_TITLE,
    APP_SUBTITLE,
    SIDEBAR_TITLE,
    MAX_CHAT_HISTORY,
    WELCOME_MESSAGE,
)

# Import limit checker
from .limit_checker import (
    init_limits_db,
    check_and_update_limit,
)

# Module exports
__all__ = [
    # Paths
    'PROJECT_ROOT',
    'DATA_DIR',
    'RAW_DATA_DIR',
    'PROCESSED_DATA_DIR',
    'DB_DIR',
    
    # Database files
    'FAISS_INDEX_PATH',
    'BM25_INDEX_PATH',
    'DOCUMENTS_PATH',
    'ENRICHED_DATA_PATH',
    'RAW_LINKS_PATH',
    
    # Model settings
    'OLLAMA_HOST',
    'OLLAMA_MODEL',
    'OLLAMA_TIMEOUT',
    'EMBEDDING_MODEL',
    'EMBEDDING_DIMENSION',
    
    # Processing settings
    'BATCH_SIZE',
    'MAX_WORKERS',
    'CHUNK_SIZE',
    'CHUNK_OVERLAP',
    'MIN_CONTENT_LENGTH',
    'MAX_REQUESTS_PER_MINUTE',
    'DAILY_USER_QUOTA',
    
    # Search settings
    'TOP_K_RESULTS',
    'HYBRID_ALPHA',
    'SIMILARITY_THRESHOLD',
    'MAX_RESPONSE_TOKENS',
    'TEMPERATURE',
    'SYSTEM_PROMPT',
    
    # UI settings
    'APP_TITLE',
    'APP_SUBTITLE',
    'SIDEBAR_TITLE',
    'MAX_CHAT_HISTORY',
    'WELCOME_MESSAGE',
    
    # Functions
    'init_limits_db',
    'check_and_update_limit',
]