"""
Olympia Academia - Data Processing Module
==========================================

This module handles AI enrichment of scraped content using Ollama/DeepSeek.

Components:
-----------
- batch_processor: Batch processing of links with AI enrichment

Author: Olympia Academia Team
"""

__version__ = "1.0.0"
__author__ = "Olympia Academia Team"

# Path Configuration
from pathlib import Path

PROJECT_ROOT = Path("D:/college/Olympia Academia/oa_chatbot/olympia-academia")
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

# Ensure directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# File paths
INPUT_FILE = PROCESSED_DIR / "oa_cleaned.xlsx"
OUTPUT_FILE = PROCESSED_DIR / "oa_enriched.xlsx"

# Module exports
__all__ = [
    'INPUT_FILE',
    'OUTPUT_FILE',
    'PROCESSED_DIR',
]